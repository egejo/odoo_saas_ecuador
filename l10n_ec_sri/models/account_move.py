# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from datetime import datetime

class AccountMove(models.Model):
    _inherit = 'account.move'

    l10n_ec_sri_status = fields.Selection([
        ('draft', 'Draft (Not Sent)'),
        ('sent', 'Sent to SRI'),
        ('authorized', 'Authorized'),
        ('rejected', 'Rejected'),
    ], string='SRI Status', default='draft', copy=False, index=True)

    l10n_ec_sri_access_key = fields.Char(string='Clave de Acceso', copy=False, size=49)
    l10n_ec_authorization_date = fields.Datetime(string='Authorization Date', copy=False)
    l10n_ec_xml_content = fields.Binary(string='Signed XML', copy=False, attachment=True)
    l10n_ec_sri_error = fields.Text(string='SRI Error Message', copy=False)

    def action_send_sri(self):
        """
        Orchestrator: Key Gen -> XML Gen -> Sign -> Send
        """
        for move in self:
            if move.l10n_ec_sri_status in ['authorized', 'sent']:
                continue

            # 1. Generate Access Key
            if not move.l10n_ec_sri_access_key:
                move.l10n_ec_sri_access_key = self.env['l10n_ec.sri.xml'].generate_access_key(move)

            # 2. Render XML
            # Assuming 'l10n_ec_sri.xml_invoice_v_2_26' exists and returns bytes or str
            xml_content = self.env['l10n_ec.sri.xml'].render_xml(move)
            if not isinstance(xml_content, bytes):
                 xml_content = xml_content.encode('utf-8')

            # 3. Sign XML
            signed_xml = self._sign_xml(xml_content)
            move.l10n_ec_xml_content = base64.b64encode(signed_xml)

            # 4. Send to SRI (Real Call)
            response = self.env['l10n_ec.sri.service'].send_document(
                signed_xml,
                environment=move.company_id.l10n_ec_sri_environment
            )

            if response.get('status') == 'RECIBIDA':
                move.l10n_ec_sri_status = 'sent'
                move.l10n_ec_sri_error = False
                # Schedule Authorization Check (Optional: Immediate check)
            else:
                move.l10n_ec_sri_status = 'rejected'
                move.l10n_ec_sri_error = "\n".join(response.get('messages', []))


    def action_check_sri(self):
        """
        Ping Check Status service (Real Implementation)
        """
        for move in self:
            if not move.l10n_ec_sri_access_key:
                raise UserError(_("No Access Key generated yet."))

            response = self.env['l10n_ec.sri.service'].check_authorization(move.l10n_ec_sri_access_key)

            if response.get('status') == 'AUTORIZADO':
                move.l10n_ec_sri_status = 'authorized'
                if response.get('date'):
                    # Parse date if necessary, assuming datetime object or ISO string from service
                    move.l10n_ec_authorization_date = response['date']

                # Store authorized XML if provided in response
                if response.get('authorized_xml'):
                    move.l10n_ec_xml_content = base64.b64encode(response['authorized_xml'].encode('utf-8'))
            elif response.get('status') == 'NO AUTORIZADO':
                move.l10n_ec_sri_status = 'rejected'
                move.l10n_ec_sri_error = "\n".join(response.get('messages', []))


    def _sign_xml(self, xml_content):
        """
        Internal helper to call the signer lib.
        """
        self.ensure_one()
        certificate = self.company_id.l10n_ec_certificate_id
        if not certificate:
            raise UserError(_("No active Electronic Signature found for this company."))

        # REAL IMPLEMENTATION
        # Pass the raw XML and the encrypted P12 data to the signer service
        return self.env['l10n_ec.sri.signer'].sign_xml(
            xml_content,
            certificate.content, # Binary field
            certificate.password # Decrypt if needed, here passed as stored
        )
