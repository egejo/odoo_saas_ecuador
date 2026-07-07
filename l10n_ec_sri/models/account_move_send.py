# -*- coding: utf-8 -*-
from odoo import models


class AccountMoveSend(models.AbstractModel):
    """
    Adjunta el XML firmado/autorizado (ademas del RIDE PDF) al correo que
    el asistente "Enviar e Imprimir" manda al cliente.

    Normativa vigente: Resolucion NAC-DGERCGC18-00000233 (RO 2do Sup. 255,
    05-jun-2018, en vigor sin reformas sobre este punto -- la reforma mas
    reciente, NAC-DGERCGC25-00000014 de 27-jun-2025, solo modifica sus
    articulos 5 y 7, sobre anulacion de comprobantes, no el articulo 6),
    Art. 6 "Entrega de comprobantes electronicos": el comprobante se
    entiende entregado cuando el emisor envia AL CORREO del adquirente
    tanto el archivo XML como la representacion impresa (RIDE). El mismo
    articulo aclara que si "solo esté disponible uno de los dos archivos
    requeridos (XML o RIDE) (...) constituye falta de entrega al
    receptor" -- es decir, mandar unicamente el RIDE (el comportamiento
    por defecto de Odoo, que solo adjunta move.invoice_pdf_report_id) no
    cumple la normativa.
    """

    _inherit = "account.move.send"

    def _get_invoice_extra_attachments(self, move):
        attachments = super()._get_invoice_extra_attachments(move)
        if (
            move.country_code == "EC"
            and move.l10n_latam_use_documents
            and move.l10n_ec_sri_status == "authorized"
        ):
            attachments |= move._l10n_ec_get_xml_attachment()
        return attachments
