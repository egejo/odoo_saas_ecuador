# -*- coding: utf-8 -*-
from odoo import models, fields, _
import base64
import re
from datetime import datetime
from odoo.exceptions import UserError

# Tabla 21 del SRI (Ficha Tecnica ATS): cada porcentaje de retencion de IVA
# tiene su propio campo obligatorio en el XML (no un catalogo por codigo
# como en el bloque AIR de renta). account.retention.line.tax_id.percentage
# ya trae exactamente estos 6 valores (10/20/30/50/70/100), confirmado
# contra produccion (l10n_ec.withholding.tax, auditado 2026-07-08).
_IVA_RETENTION_ATS_FIELD_BY_PERCENT = {
    10.0: "valRetBien10",
    20.0: "valRetServ20",
    30.0: "valorRetBienes",
    50.0: "valRetServ50",
    70.0: "valorRetServicios",
    100.0: "valRetServ100",
}

# account.tax.group.l10n_ec_type: catalogo que ya trae el modulo CORE de
# Odoo Community l10n_ec (no es un campo de este fork ni de Enterprise),
# confirmado por SQL contra produccion -- todas las tasas de IVA/ICE
# realmente aplicadas en facturas ya lo tienen poblado correctamente.
_VAT_NOT_ZERO_TYPES = ("vat05", "vat08", "vat12", "vat13", "vat14", "vat15")
_VAT_ZERO_TYPES = ("zero_vat", "not_charged_vat", "exempt_vat")

# Tabla 4 de la Ficha Tecnica ATS: en el modulo de VENTAS, factura (01) y
# nota o boleta de venta (02) siempre se reportan bajo el codigo generico
# 18 ("Documentos autorizados utilizados en ventas excepto N/C N/D"); NC
# (04) y ND (05) conservan su propio codigo. Confirmado tambien en
# Enterprise l10n_ec_reports_ats (ATS_SALE_DOCUMENT_TYPE).
_ATS_SALE_DOCUMENT_TYPE = {"01": "18", "02": "18"}

_DOC_NUMBER_RE = re.compile(r"(\d{1,3})-(\d{1,3})-(\d{1,9})")


class L10nEcAtsWizard(models.TransientModel):
    _name = "l10n_ec.ats.wizard"
    _description = "Anexo Transaccional Simplificado (ATS) Wizard"

    date_month = fields.Selection(
        [
            ("01", "January"),
            ("02", "February"),
            ("03", "March"),
            ("04", "April"),
            ("05", "May"),
            ("06", "June"),
            ("07", "July"),
            ("08", "August"),
            ("09", "September"),
            ("10", "October"),
            ("11", "November"),
            ("12", "December"),
        ],
        string="Month",
        required=True,
        default=lambda self: datetime.now().strftime("%m"),
    )

    date_year = fields.Char(
        string="Year", required=True, default=lambda self: datetime.now().strftime("%Y")
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )

    # Result
    xml_data = fields.Binary("ATS XML", readonly=True)
    xml_filename = fields.Char(string="Filename", readonly=True)

    def action_generate_ats(self):
        self.ensure_one()
        xml_content = self.generate_xml()
        self.xml_data = base64.b64encode(xml_content)
        self.xml_filename = (
            f"ATS_{self.date_month}_{self.date_year}_{self.company_id.vat}.xml"
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "l10n_ec.ats.wizard",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
        }

    def action_print_form103(self):
        self.ensure_one()
        data = self._get_ats_data()

        # Prepare data for Form 103 (Retentions), grouped by tax code
        retention_summary = {}
        for p in data["purchases"]:
            for r in p.get("retentions", []):
                code = r["code"]
                if code not in retention_summary:
                    retention_summary[code] = {
                        "code": code,
                        "name": r.get("name") or ("Retention " + code),
                        "base": 0.0,
                        "percent": r["percent"],
                        "amount": 0.0,
                    }
                retention_summary[code]["base"] += r["base"]
                retention_summary[code]["amount"] += r["val"]

        report_data = {
            "period": f"{self.date_month}/{self.date_year}",
            "retentions": sorted(retention_summary.values(), key=lambda x: x["code"]),
        }
        return self.env.ref("l10n_ec_reports.action_report_form_103").report_action(
            self, data={"data": report_data}
        )

    def action_print_form104(self):
        self.ensure_one()
        data = self._get_ats_data()

        # Form 104 es la declaracion neta de IVA: a diferencia del detalle
        # del ATS (donde cada documento, factura o NC, lleva su propio
        # valor positivo), aqui una nota de credito SI debe restar --
        # net_sign ya distingue eso (-1 solo para credit_note).
        sales_base = sum(
            s["net_sign"] * (s["baseImponible"] + s["baseImpGrav"] + s["baseNoGraIva"])
            for s in data["sales"]
        )
        sales_iva = sum(s["net_sign"] * s["montoIva"] for s in data["sales"])
        sales_ice = sum(s["net_sign"] * s.get("montoIce", 0.0) for s in data["sales"])

        purchases_base = sum(
            p["net_sign"]
            * (p["baseImponible"] + p["baseImpGrav"] + p["baseNoGraIva"] + p["baseImpExe"])
            for p in data["purchases"]
        )
        purchases_iva = sum(p["net_sign"] * p["montoIva"] for p in data["purchases"])
        purchases_ice = sum(
            p["net_sign"] * p.get("montoIce", 0.0) for p in data["purchases"]
        )

        report_data = {
            "period": f"{self.date_month}/{self.date_year}",
            "sales_base": sales_base,
            "sales_iva": sales_iva,
            "purchases_base": purchases_base,
            "purchases_iva": purchases_iva,
            "ice_payable": sales_ice,
            "ice_credit": purchases_ice,
        }
        return self.env.ref("l10n_ec_reports.action_report_form_104").report_action(
            self, data={"data": report_data}
        )

    def generate_xml(self):
        data = self._get_ats_data()
        values = {
            "wizard": self,
            "company": self.company_id,
            "purchases": data["purchases"],
            "sales": data["sales"],
            "cancelled": data["cancelled"],
            "num_estab_ruc": data["num_estab_ruc"],
            "establecimientos": data["establecimientos"],
            # Tabla 20: las ventas electronicas (E) no se suman al talon
            # resumen -- solo las fisicas (F). Adrenasports factura 100%
            # electronico, asi que en la practica esto sera 0.00, y es lo
            # correcto (el detalle ya viaja al SRI en el XML de cada
            # factura individual).
            "total_sales": sum(
                s["net_sign"] * (s["baseImponible"] + s["baseImpGrav"] + s["baseNoGraIva"])
                for s in data["sales"]
                if s["tipoEm"] == "F"
            ),
            "format_float": lambda x, p: ("%." + str(p) + "f") % x,
        }
        xml_content = self.env["ir.qweb"]._render(
            "l10n_ec_reports.l10n_ec_ats_xml", values
        )
        return xml_content.encode("utf-8")

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _split_document_number(self, number):
        """Descompone 'NNN-NNN-NNNNNNNNN' (con o sin prefijo tipo 'Fact ')
        en establecimiento/punto de emision/secuencial, zero-padded segun
        la Ficha Tecnica ATS. Si no calza el patron, se devuelven ceros
        para que el error sea visible al revisar el XML en vez de
        colarse como un valor plausible pero falso."""
        match = number and _DOC_NUMBER_RE.search(number)
        if not match:
            return "000", "000", "000000000"
        estab, pto, sec = match.groups()
        return estab.zfill(3), pto.zfill(3), sec.zfill(9)

    def _get_ats_partner_id_type_code(self, partner, sale):
        """Tabla 2 de la Ficha Tecnica ATS."""
        id_type = partner.l10n_ec_identifier_type
        if sale:
            return {"ruc": "04", "cedula": "05"}.get(id_type, "06")
        return {"ruc": "01", "cedula": "02"}.get(id_type, "03")

    def _get_move_base_amounts(self, move):
        """Bases por linea segun el tipo de IVA real de cada linea
        (account.tax.group.l10n_ec_type, catalogo del modulo core l10n_ec,
        no de este fork -- confirmado poblado correctamente en produccion
        para todas las tasas de IVA/ICE realmente usadas)."""
        base_0 = base_grav = base_exe = base_no_obj = 0.0
        for line in move.invoice_line_ids.filtered(
            lambda l: l.display_type not in ("line_section", "line_note")
        ):
            vat_taxes = line.tax_ids.filtered(
                lambda t: t.tax_group_id.l10n_ec_type in (_VAT_NOT_ZERO_TYPES + _VAT_ZERO_TYPES)
            )
            ec_type = vat_taxes[:1].tax_group_id.l10n_ec_type if vat_taxes else "zero_vat"
            amount = abs(line.balance)
            if ec_type in _VAT_NOT_ZERO_TYPES:
                base_grav += amount
            elif ec_type == "exempt_vat":
                base_exe += amount
            elif ec_type == "not_charged_vat":
                base_no_obj += amount
            else:
                base_0 += amount
        return base_0, base_grav, base_exe, base_no_obj

    def _get_move_tax_amounts(self, move):
        monto_iva = monto_ice = 0.0
        for line in move.line_ids.filtered(lambda l: l.tax_line_id):
            ec_type = line.tax_line_id.tax_group_id.l10n_ec_type
            if ec_type == "ice":
                monto_ice += abs(line.balance)
            elif ec_type in _VAT_NOT_ZERO_TYPES:
                monto_iva += abs(line.balance)
        return monto_iva, monto_ice

    def _get_document_modification_vals(self, move):
        """docModificado/estabModificado/... obligatorios en NC/ND
        (Tabla 4), enlazando a la factura original via reversed_entry_id
        (NC) o debit_origin_id (ND, wizard nativo account_debit_note)."""
        if move.l10n_latam_document_type_id.internal_type not in (
            "credit_note",
            "debit_note",
        ):
            return {}
        modified = move.reversed_entry_id or move.debit_origin_id
        if not modified:
            return {}
        m_estab, m_pto, m_sec = self._split_document_number(
            modified.l10n_latam_document_number
        )
        return {
            "docModificado": modified.l10n_latam_document_type_id.code or "",
            "estabModificado": m_estab,
            "ptoEmiModificado": m_pto,
            "secModificado": m_sec,
            "autModificado": modified.l10n_ec_sri_access_key or "9999999999",
        }

    def _get_period_bounds(self):
        try:
            date_start = datetime.strptime(
                f"{self.date_year}-{self.date_month}-01", "%Y-%m-%d"
            ).date()
            if self.date_month == "12":
                date_end = datetime.strptime(
                    f"{int(self.date_year) + 1}-01-01", "%Y-%m-%d"
                ).date()
            else:
                date_end = datetime.strptime(
                    f"{self.date_year}-{int(self.date_month) + 1:02d}-01", "%Y-%m-%d"
                ).date()
        except ValueError:
            raise UserError(_("Invalid Date Configuration"))
        return date_start, date_end

    # =========================================================================
    # CORE
    # =========================================================================

    def _get_ats_data(self):
        """
        Core logic to fetch and aggregate data for ATS, Form 103, and Form 104.
        """
        date_start, date_end = self._get_period_bounds()

        purchases_data = self._get_purchases_data(date_start, date_end)
        sales_data = self._get_sales_data(date_start, date_end)

        estabs = {p["estab"] for p in purchases_data} | {
            s["estab"] for s in sales_data
        }

        return {
            "purchases": purchases_data,
            "sales": sales_data,
            "cancelled": self._get_cancelled_documents(date_start, date_end),
            "num_estab_ruc": max(len(estabs), 1),
            "establecimientos": sorted(estabs) or ["001"],
        }

    def _get_purchases_data(self, date_start, date_end):
        domain_in = [
            ("move_type", "in", ("in_invoice", "in_refund")),
            ("invoice_date", ">=", date_start),
            ("invoice_date", "<", date_end),
            ("state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
        ]
        purchases_data = []

        for inv in self.env["account.move"].search(domain_in):
            tp_id = self._get_ats_partner_id_type_code(inv.partner_id, sale=False)
            estab, pto, sec = self._split_document_number(
                inv.l10n_latam_document_number
            )
            base_0, base_grav, base_exe, base_no_obj = self._get_move_base_amounts(inv)
            monto_iva, monto_ice = self._get_move_tax_amounts(inv)

            # Retenciones (AIR de renta + desglose de IVA por tarifa)
            retentions_recs = self.env["account.retention"].search(
                [("invoice_id", "=", inv.id), ("state", "=", "posted")]
            )
            air_data = []
            iva_ret_vals = dict.fromkeys(_IVA_RETENTION_ATS_FIELD_BY_PERCENT.values(), 0.0)
            ret_info = {
                "estabRet": "000",
                "ptoEmiRet": "000",
                "secRet": "000000000",
                "autRet": "0000000000",
                "fechaEmiRet": "",
            }

            if retentions_recs:
                main_ret = retentions_recs[0]
                ret_info["estabRet"], ret_info["ptoEmiRet"], ret_info["secRet"] = (
                    self._split_document_number(main_ret.name)
                )
                ret_info["autRet"] = main_ret.l10n_ec_sri_access_key or "0000000000"
                ret_info["fechaEmiRet"] = main_ret.date.strftime("%d/%m/%Y")

                for line in main_ret.retention_line_ids:
                    if line.tax_type == "renta":
                        air_data.append(
                            {
                                "code": line.tax_code,
                                "name": line.tax_id.name,
                                "base": line.base,
                                "percent": line.percentage,
                                "val": line.amount,
                            }
                        )
                    elif line.tax_type == "iva":
                        field = _IVA_RETENTION_ATS_FIELD_BY_PERCENT.get(line.percentage)
                        if field:
                            iva_ret_vals[field] += line.amount

            purchases_data.append(
                {
                    "sustento": inv.l10n_ec_sustento_code or "01",
                    "tpIdProv": tp_id,
                    "idProv": inv.partner_id.vat,
                    "tipoComprobante": inv.l10n_latam_document_type_id.code or "01",
                    "parteRel": (
                        "SI"
                        if inv.partner_id.commercial_partner_id.l10n_ec_related_party
                        else "NO"
                    ),
                    "fechaRegistro": inv.date.strftime("%d/%m/%Y"),
                    "estab": estab,
                    "ptoEmi": pto,
                    "secuencial": sec,
                    "fechaEmision": inv.invoice_date.strftime("%d/%m/%Y"),
                    "autorizacion": inv.l10n_ec_sri_access_key or "9999999999",
                    "baseNoGraIva": base_no_obj,
                    "baseImponible": base_0,
                    "baseImpGrav": base_grav,
                    "baseImpExe": base_exe,
                    "montoIce": monto_ice,
                    "montoIva": monto_iva,
                    # Igual que en ventas: el detalle siempre lleva el
                    # valor propio (positivo) del documento; net_sign
                    # sirve solo para los agregados (Form 103/104), donde
                    # una nota de credito de compra sí debe restar.
                    "net_sign": (
                        -1
                        if inv.l10n_latam_document_type_id.internal_type == "credit_note"
                        else 1
                    ),
                    "retentions": air_data,
                    **iva_ret_vals,
                    **ret_info,
                    **self._get_document_modification_vals(inv),
                }
            )

        return purchases_data

    def _get_sales_data(self, date_start, date_end):
        domain_out = [
            ("move_type", "in", ("out_invoice", "out_refund")),
            ("invoice_date", ">=", date_start),
            ("invoice_date", "<", date_end),
            ("state", "=", "posted"),
            ("company_id", "=", self.company_id.id),
        ]
        out_moves = self.env["account.move"].search(domain_out)

        # Se agrupa por cliente + tipo de documento + tipo de emision
        # (electronica/fisica), igual que exige la Ficha Tecnica ATS.
        sales_agg = {}

        for inv in out_moves:
            partner = inv.partner_id.commercial_partner_id
            dtype = inv.l10n_latam_document_type_id
            tipo_em = "E" if inv.l10n_ec_sri_access_key else "F"
            key = (partner.id, dtype.id, tipo_em)

            if key not in sales_agg:
                estab, _pto, _sec = self._split_document_number(
                    inv.l10n_latam_document_number
                )
                sales_agg[key] = {
                    "partner": partner,
                    "dtype": dtype,
                    "tipoEm": tipo_em,
                    "estab": estab,
                    # Nota de credito resta del talon resumen fisico
                    # (ventasEstablecimiento/total_sales); factura y nota
                    # de debito suman. Cada fila del detalle siempre lleva
                    # su propio valor positivo (son documentos distintos,
                    # con su propio tipoComprobante), la resta solo aplica
                    # al agregado por establecimiento.
                    "net_sign": -1 if dtype.internal_type == "credit_note" else 1,
                    "baseNoGraIva": 0.0,
                    "baseImponible": 0.0,
                    "baseImpGrav": 0.0,
                    "montoIva": 0.0,
                    "montoIce": 0.0,
                    "count": 0,
                    "doc_mod": {},
                }

            agg = sales_agg[key]
            base_0, base_grav, base_exe, base_no_obj = self._get_move_base_amounts(inv)
            monto_iva, monto_ice = self._get_move_tax_amounts(inv)

            agg["baseImponible"] += base_0
            agg["baseImpGrav"] += base_grav
            agg["baseNoGraIva"] += base_exe + base_no_obj
            agg["montoIva"] += monto_iva
            agg["montoIce"] += monto_ice
            agg["count"] += 1

            if not agg["doc_mod"]:
                agg["doc_mod"] = self._get_document_modification_vals(inv)

        sales_data = []
        for (_pid, _dtype_id, _tipo_em), val in sales_agg.items():
            partner = val["partner"]
            doc_code = val["dtype"].code or "18"
            sales_data.append(
                {
                    "tpIdCliente": self._get_ats_partner_id_type_code(
                        partner, sale=True
                    ),
                    "idCliente": partner.vat,
                    "parteRel": "SI" if partner.l10n_ec_related_party else "NO",
                    "tipoComprobante": _ATS_SALE_DOCUMENT_TYPE.get(doc_code, doc_code),
                    "tipoEm": val["tipoEm"],
                    "estab": val["estab"],
                    "net_sign": val["net_sign"],
                    "count": val["count"],
                    "baseImpGrav": val["baseImpGrav"],
                    "baseImponible": val["baseImponible"],
                    "baseNoGraIva": val["baseNoGraIva"],
                    "montoIva": val["montoIva"],
                    "montoIce": val["montoIce"],
                    # Sin fuente de datos: este sistema no modela
                    # retenciones que los CLIENTES le hacen a Adrenasports
                    # (solo las que Adrenasports hace a sus proveedores,
                    # via account.retention). Limitacion conocida.
                    "valorRetIva": 0.0,
                    "valorRetRenta": 0.0,
                    **val["doc_mod"],
                }
            )
        return sales_data

    def _get_cancelled_documents(self, date_start, date_end):
        domain = [
            ("move_type", "in", ("out_invoice", "out_refund", "in_invoice", "in_refund")),
            ("invoice_date", ">=", date_start),
            ("invoice_date", "<", date_end),
            ("state", "=", "cancel"),
            ("company_id", "=", self.company_id.id),
        ]
        data = []
        for inv in self.env["account.move"].search(domain):
            estab, pto, sec = self._split_document_number(
                inv.l10n_latam_document_number
            )
            data.append(
                {
                    "tipo": inv.l10n_latam_document_type_id.code or "01",
                    "estab": estab,
                    "pto": pto,
                    "sec": sec,
                    "aut": inv.l10n_ec_sri_access_key or "0000000000",
                }
            )

        retention_domain = [
            ("date", ">=", date_start),
            ("date", "<", date_end),
            ("state", "=", "cancel"),
            ("company_id", "=", self.company_id.id),
        ]
        for ret in self.env["account.retention"].search(retention_domain):
            estab, pto, sec = self._split_document_number(ret.name)
            data.append(
                {
                    "tipo": "07",
                    "estab": estab,
                    "pto": pto,
                    "sec": sec,
                    "aut": ret.l10n_ec_sri_access_key or "0000000000",
                }
            )
        return data
