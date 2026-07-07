# -*- coding: utf-8 -*-
from odoo import models, api
from odoo.exceptions import ValidationError
import random
import logging

_logger = logging.getLogger(__name__)


class L10nEcSriXml(models.AbstractModel):
    _name = "l10n_ec.sri.xml"
    _description = "SRI XML Generator"

    @api.model
    def generate_access_key(self, record):
        """
        Generate 49-digit Access Key.
        Format:
        [0:8]   Date (DDMMYYYY)
        [8:10]  Doc Type (01)
        [10:23] RUC (1234567890001)
        [23:24] Environment (1 or 2)
        [24:30] Establisment/Series (001-001) -> 001001
        [30:39] Sequential (000000001)
        [39:47] Random Number (8 digits)
        [47:48] Emission Type (1)
        [48:49] Verifier Digit (Mod 11)
        """
        # 1. Extraction
        date_inv = record.invoice_date.strftime("%d%m%Y")
        doc_type = record.l10n_latam_document_type_id.code  # e.g., '01'
        ruc = record.company_id.vat
        env = "1" if record.company_id.l10n_ec_sri_environment == "test" else "2"

        # Split Journal: 001-001
        try:
            entity, emission = record.journal_id.code.split(
                "-"
            )  # Simplified extraction hook
            serie = f"{entity}{emission}"
        except:
            # Fallback for now or use fields from journal extension
            # In real implementation, use l10n_ec_entity from `account.journal`
            serie = f"{record.journal_id.l10n_ec_entity}{record.journal_id.l10n_ec_emission}"

        sequential = f"{record.name.split('-')[-1]:0>9}"  # Extract sequence number

        # Random 8 digits
        code_numeric = f"{random.randint(1, 99999999):08d}"
        emission_type = "1"  # Normal

        # 2. Construction (Pre-Verifier)
        base_key = f"{date_inv}{doc_type}{ruc}{env}{serie}{sequential}{code_numeric}{emission_type}"

        # 3. Check Digit (Modulo 11)
        verifier = self._get_modulo_11(base_key)

        access_key = f"{base_key}{verifier}"

        if len(access_key) != 49:
            raise ValidationError(
                f"Generated Access Key length is {len(access_key)}, expected 49."
            )

        return access_key

    def _get_modulo_11(self, key):
        """
        Standard SRI Modulo 11 Algorithm
        """
        key = key[::-1]
        total = 0
        factor = 2

        for char in key:
            total += int(char) * factor
            factor += 1
            if factor > 7:
                factor = 2

        remainder = total % 11
        check_digit = 11 - remainder

        if check_digit == 11:
            check_digit = 0
        elif check_digit == 10:
            check_digit = 1

        return str(check_digit)

    # tabla17/tabla18 del Comprobante Electronico SRI, tal como documentado en
    # docs/05_data_mapping/DM_01_ELECTRONIC_INVOICE.md. Solo se incluyen las
    # tarifas realmente usadas en este catalogo (0%, 5%, 12%, 14%, 15% +
    # no objeto/exento); cualquier otra levanta error en vez de mandar un
    # codigo adivinado al SRI.
    _TABLA17_CODIGO_IMPUESTO = {
        "vat05": "2", "vat08": "2", "vat12": "2", "vat13": "2", "vat14": "2",
        "vat15": "2", "zero_vat": "2", "not_charged_vat": "2", "exempt_vat": "2",
        "ice": "3",
        "irbpnr": "5",
    }
    _TABLA18_CODIGO_PORCENTAJE = {
        "zero_vat": "0",
        "not_charged_vat": "6",
        "exempt_vat": "7",
        "vat05": "5",
        "vat12": "2",
        "vat14": "3",
        "vat15": "4",
    }
    # Mapea partner._l10n_ec_get_identification_type() (l10n_ec core) al
    # catalogo SRI de tipoIdentificacionComprador.
    _TIPO_IDENTIFICACION = {
        "ruc": "04",
        "cedula": "05",
        "ec_passport": "06",
        "passport": "06",
        "foreign": "08",
    }

    def _get_buyer_identification_code(self, record):
        partner_type = record.partner_id._l10n_ec_get_identification_type()
        return self._TIPO_IDENTIFICACION.get(partner_type, "05")

    def _map_tax_codes(self, tax):
        ec_type = tax.tax_group_id.l10n_ec_type
        if (
            ec_type not in self._TABLA17_CODIGO_IMPUESTO
            or ec_type not in self._TABLA18_CODIGO_PORCENTAJE
        ):
            raise ValidationError(
                "El impuesto '%s' (tipo SRI '%s') no tiene codigo de "
                "catalogo SRI (tabla17/tabla18) configurado. Agrega el "
                "mapeo en l10n_ec_sri_xml.py antes de enviar esta "
                "factura al SRI." % (tax.name, ec_type or "sin definir")
            )
        return self._TABLA17_CODIGO_IMPUESTO[ec_type], self._TABLA18_CODIGO_PORCENTAJE[ec_type]

    def _get_tax_breakdown(self, record):
        """
        Agrega los impuestos de la factura para <totalConImpuestos>.
        """
        breakdown = []
        for line in record.line_ids.filtered(lambda l: l.tax_line_id):
            codigo, codigo_porcentaje = self._map_tax_codes(line.tax_line_id)
            breakdown.append(
                {
                    "codigo": codigo,
                    "codigo_porcentaje": codigo_porcentaje,
                    "tarifa": line.tax_line_id.amount,
                    "base_imponible": abs(line.tax_base_amount),
                    "valor": abs(line.balance),
                }
            )
        return breakdown

    def _get_line_taxes(self, line):
        """
        Impuestos aplicados a una linea de detalle, para <detalle>/<impuestos>.
        """
        result = []
        for tax in line.tax_ids:
            codigo, codigo_porcentaje = self._map_tax_codes(tax)
            result.append(
                {
                    "codigo": codigo,
                    "codigo_porcentaje": codigo_porcentaje,
                    "tarifa": tax.amount,
                    "base_imponible": line.price_subtotal,
                    "valor": line.price_subtotal * tax.amount / 100,
                }
            )
        return result

    @api.model
    def render_xml(self, record):
        """
        Render the XML using QWeb template.

        Dispatches by move_type: facturas (codDoc 01) and notas de credito
        (codDoc 04) use different SRI schemas. Before this, every document
        type was rendered as xml_invoice regardless of move_type, so a
        credit note sharing the invoice's estab/ptoEmi/secuencial looked to
        the SRI like the exact same already-authorized factura ("ERROR
        SECUENCIAL REGISTRADO").

        Una nota de debito NO tiene move_type propio (Odoo la crea con
        move_type='out_invoice' + debit_origin_id, via el wizard nativo
        "Add Debit Note" de account_debit_note) -- se distingue por
        l10n_latam_document_type_id.code, no por move_type.
        """
        if record.move_type == "out_refund":
            return self._render_credit_note_xml(record)
        if record.l10n_latam_document_type_id.code == "05":
            return self._render_debit_note_xml(record)

        values = {
            "record": record,
            "access_key": record.l10n_ec_sri_access_key,
            "tipo_identificacion_comprador": self._get_buyer_identification_code(record),
            "tax_breakdown": self._get_tax_breakdown(record),
            "line_taxes": {
                line.id: self._get_line_taxes(line) for line in record.invoice_line_ids
            },
        }
        return self.env["ir.qweb"]._render("l10n_ec_sri.xml_invoice", values)

    @api.model
    def _render_credit_note_xml(self, record):
        original_invoice = record.reversed_entry_id
        if not original_invoice:
            raise ValidationError(
                "La nota de credito '%s' no tiene una factura original "
                "vinculada (reversed_entry_id vacio). El SRI exige "
                "codDocModificado/numDocModificado/fechaEmisionDocSustento "
                "de la factura que se esta rectificando." % record.name
            )
        values = {
            "record": record,
            "access_key": record.l10n_ec_sri_access_key,
            "tipo_identificacion_comprador": self._get_buyer_identification_code(record),
            "tax_breakdown": self._get_tax_breakdown(record),
            "line_taxes": {
                line.id: self._get_line_taxes(line) for line in record.invoice_line_ids
            },
            "original_invoice": original_invoice,
            "motivo": record.narration or record.name or "NOTA DE CREDITO",
        }
        return self.env["ir.qweb"]._render("l10n_ec_sri.xml_credit_note", values)

    @api.model
    def _render_debit_note_xml(self, record):
        """
        Nota de Debito (codDoc 05). A diferencia de la nota de credito,
        Odoo la vincula al comprobante original via debit_origin_id (no
        reversed_entry_id) -- ver account_debit_note (wizard nativo
        "Add Debit Note", ya instalado). El schema tampoco tiene
        <detalles> por linea de producto: solo <motivos> (razon + valor
        por linea) y un <impuestos> agregado a nivel de cabecera.
        """
        original_invoice = record.debit_origin_id
        if not original_invoice:
            raise ValidationError(
                "La nota de debito '%s' no tiene un comprobante original "
                "vinculado (debit_origin_id vacio). El SRI exige "
                "codDocModificado/numDocModificado/fechaEmisionDocSustento "
                "del comprobante que se esta afectando." % record.name
            )
        values = {
            "record": record,
            "access_key": record.l10n_ec_sri_access_key,
            "tipo_identificacion_comprador": self._get_buyer_identification_code(record),
            "tax_breakdown": self._get_tax_breakdown(record),
            "original_invoice": original_invoice,
        }
        return self.env["ir.qweb"]._render("l10n_ec_sri.xml_debit_note", values)
