# -*- coding: utf-8 -*-
"""
Importacion de comprobantes electronicos SRI RECIBIDOS de proveedores
(vendor bills). Un vendor bill es un comprobante que el PROVEEDOR ya
emitio y transmitio al SRI -- Odoo nunca lo genera ni lo envia (ver
action_send_sri en account_move.py, que ahora rechaza explicitamente
estos moves). Antes de esto, cargar una factura de compra recibida en
XML implicaba transcribir a mano cada linea/impuesto.

Este importador engancha el mecanismo NATIVO de Odoo (Community, no
requiere Enterprise) para "crear factura desde adjunto": arrastrar el
XML sobre la lista de Vendor Bills, o adjuntarlo al chatter de una
factura ya creada, dispara account.move._extend_with_attachments(), que
busca un decoder via _get_edi_decoder() -- el mismo hook que usa
account_edi_ubl_cii (tambien Community/LGPL-3) para UBL/CII. Ver
/usr/lib/python3/dist-packages/odoo/addons/account/models/account_move.py
y .../account_edi_ubl_cii/models/account_edi_common.py como referencia
de patron (ambos LGPL-3, parte de la imagen oficial odoo:18).

Resolucion de lineas: igual que el importador UBL nativo, se busca un
product.product existente por codigoPrincipal/codigoAuxiliar (barcode/
default_code) o por nombre; si no hay match, la linea queda sin producto
(solo descripcion/cantidad/precio/impuesto) en vez de auto-crear un
producto o forzar una cuenta generica -- el documento queda en borrador
para que el usuario revise antes de contabilizar.
"""
import logging

from lxml import etree

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# codDoc/tag raiz del SRI -> move_type de Odoo. Guia de remision y
# liquidacion de compra no generan una factura de proveedor por si
# solas, se dejan fuera a proposito.
_SRI_MOVE_TYPE = {
    "factura": "in_invoice",
    "notaCredito": "in_refund",
}
_SRI_DOCUMENT_CODE = {
    "factura": "01",
    "notaCredito": "04",
}


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_edi_decoder(self, file_data, new=False):
        # EXTENDS 'account'
        if file_data.get("type") == "xml":
            root = self._l10n_ec_sri_unwrap_comprobante(file_data.get("xml_tree"))
            if root is not None and root.tag in _SRI_MOVE_TYPE:
                return self._l10n_ec_sri_import_invoice
        return super()._get_edi_decoder(file_data, new=new)

    @api.model
    def _l10n_ec_sri_unwrap_comprobante(self, tree):
        """
        Un proveedor casi siempre reenvia el XML tal como se lo entrega el
        SRI tras autorizar: envuelto en
        <autorizacion><comprobante><![CDATA[<factura>...]]></comprobante>
        </autorizacion>, no el <factura> "pelado". Se desenvuelve y
        re-parsea el comprobante real desde el CDATA en ese caso.
        """
        if tree is None:
            return None
        if tree.tag == "autorizacion":
            comprobante_node = tree.find("comprobante")
            if comprobante_node is None or not comprobante_node.text:
                return None
            try:
                return etree.fromstring(comprobante_node.text.encode("utf-8"))
            except etree.XMLSyntaxError:
                _logger.warning("Import SRI: contenido de <comprobante> no es XML valido")
                return None
        return tree

    def _l10n_ec_sri_import_invoice(self, invoice, file_data, new):
        """
        Decoder registrado en _get_edi_decoder. Firma exigida por
        _extend_with_attachments: (invoice, file_data, new) -> bool.
        """
        root = self._l10n_ec_sri_unwrap_comprobante(file_data.get("xml_tree"))
        move_type = _SRI_MOVE_TYPE[root.tag]

        if not new and invoice.move_type != move_type:
            raise UserError(
                _(
                    "El XML corresponde a un(a) %(tag)s del proveedor "
                    "(debería importarse como %(expected)s), pero este "
                    "documento es %(actual)s. Impórtelo desde un "
                    "documento del tipo correcto."
                )
                % {
                    "tag": root.tag,
                    "expected": move_type,
                    "actual": invoice.move_type,
                }
            )

        info_tributaria = root.find("infoTributaria")
        clave_acceso = self._sri_text(info_tributaria, "claveAcceso")
        if clave_acceso:
            duplicate = self.search(
                [
                    ("l10n_ec_sri_access_key", "=", clave_acceso),
                    ("id", "!=", invoice._origin.id),
                ],
                limit=1,
            )
            if duplicate:
                raise UserError(
                    _(
                        "Ya existe un comprobante importado con esta clave "
                        "de acceso (%(name)s), no se importa de nuevo."
                    )
                    % {"name": duplicate.display_name}
                )

        with invoice._get_edi_creation() as invoice:
            invoice.move_type = move_type
            self._l10n_ec_sri_fill_invoice(invoice, root, info_tributaria)

        invoice.message_post(
            body=_("Comprobante importado desde XML SRI (clave de acceso: %s).")
            % (clave_acceso or _("no encontrada"))
        )
        return True

    def _l10n_ec_sri_fill_invoice(self, invoice, root, info_tributaria):
        info_node = (
            root.find("infoFactura")
            if root.tag == "factura"
            else root.find("infoNotaCredito")
        )

        ruc_emisor = self._sri_text(info_tributaria, "ruc")
        razon_social = self._sri_text(info_tributaria, "razonSocial")
        clave_acceso = self._sri_text(info_tributaria, "claveAcceso")
        estab = self._sri_text(info_tributaria, "estab")
        pto_emi = self._sri_text(info_tributaria, "ptoEmi")
        secuencial = self._sri_text(info_tributaria, "secuencial")

        partner = self.env["res.partner"]._retrieve_partner(
            name=razon_social, vat=ruc_emisor, company=invoice.company_id
        )
        if not partner and ruc_emisor:
            partner = self.env["res.partner"].create(
                {
                    "name": razon_social or ruc_emisor,
                    "vat": ruc_emisor,
                    "company_type": "company",
                    "country_id": self.env.ref("base.ec").id,
                }
            )
            _logger.info(
                "Import SRI: partner nuevo creado (%s, RUC %s) al importar %s",
                partner.name,
                ruc_emisor,
                clave_acceso,
            )
        if partner:
            invoice.partner_id = partner

        fecha_emision = self._sri_text(info_node, "fechaEmision")
        if fecha_emision and fecha_emision.count("/") == 2:
            dd, mm, yyyy = fecha_emision.split("/")
            invoice.invoice_date = fields.Date.from_string(f"{yyyy}-{mm}-{dd}")

        if estab and pto_emi and secuencial:
            invoice.ref = f"{estab}-{pto_emi}-{secuencial}"

        if clave_acceso:
            invoice.l10n_ec_sri_access_key = clave_acceso

        doc_code = _SRI_DOCUMENT_CODE.get(root.tag)
        if doc_code:
            doc_type = self.env["l10n_latam.document.type"].search(
                [("country_id.code", "=", "EC"), ("code", "=", doc_code)], limit=1
            )
            if doc_type:
                invoice.l10n_latam_document_type_id = doc_type.id

        line_commands = [fields.Command.clear()]
        for line_vals in self._l10n_ec_sri_get_line_values(root, invoice):
            line_commands.append(fields.Command.create(line_vals))
        invoice.invoice_line_ids = line_commands

    def _l10n_ec_sri_get_line_values(self, root, invoice):
        lines = []
        detalles = root.find("detalles")
        if detalles is None:
            return lines

        for detalle in detalles.findall("detalle"):
            descripcion = self._sri_text(detalle, "descripcion") or _("Sin descripción")
            codigo_principal = self._sri_text(detalle, "codigoPrincipal")
            codigo_auxiliar = self._sri_text(detalle, "codigoAuxiliar")
            cantidad = float(self._sri_text(detalle, "cantidad") or "1")
            precio_unitario = float(self._sri_text(detalle, "precioUnitario") or "0")
            descuento = float(self._sri_text(detalle, "descuento") or "0")

            discount_percent = 0.0
            if cantidad and precio_unitario:
                discount_percent = (descuento / (cantidad * precio_unitario)) * 100

            product = self.env["product.product"]._retrieve_product(
                name=descripcion,
                default_code=codigo_principal,
                barcode=codigo_auxiliar,
                company=invoice.company_id,
            )

            line_vals = {
                "name": descripcion,
                "quantity": cantidad,
                "price_unit": precio_unitario,
                "discount": discount_percent,
                "tax_ids": [
                    fields.Command.set(
                        self._l10n_ec_sri_get_line_taxes(detalle, invoice).ids
                    )
                ],
            }
            if product:
                line_vals["product_id"] = product.id
            lines.append(line_vals)

        return lines

    def _l10n_ec_sri_get_line_taxes(self, detalle, invoice):
        taxes = self.env["account.tax"]
        impuestos = detalle.find("impuestos")
        if impuestos is None:
            return taxes

        for impuesto in impuestos.findall("impuesto"):
            tarifa = self._sri_text(impuesto, "tarifa")
            if tarifa is None:
                continue
            tax = self.env["account.tax"].search(
                [
                    ("company_id", "=", invoice.company_id.id),
                    ("type_tax_use", "=", "purchase"),
                    ("amount_type", "=", "percent"),
                    ("amount", "=", float(tarifa)),
                ],
                limit=1,
            )
            if tax:
                taxes |= tax
            else:
                _logger.info(
                    "Import SRI: no se encontro impuesto de compra al %s%% "
                    "(codigo %s), la linea queda sin ese impuesto -- "
                    "revisar manualmente.",
                    tarifa,
                    self._sri_text(impuesto, "codigo"),
                )
        return taxes

    @staticmethod
    def _sri_text(node, tag):
        if node is None:
            return None
        child = node.find(tag)
        return child.text.strip() if child is not None and child.text else None
