# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import random
import logging

_logger = logging.getLogger(__name__)

class L10nEcSriXml(models.AbstractModel):
    _name = 'l10n_ec.sri.xml'
    _description = 'SRI XML Generator'

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
        date_inv = record.invoice_date.strftime('%d%m%Y')
        doc_type = record.l10n_latam_document_type_id.code  # e.g., '01'
        ruc = record.company_id.vat
        env = record.company_id.l10n_ec_sri_environment

        # Split Journal: 001-001
        try:
            entity, emission = record.journal_id.code.split('-') # Simplified extraction hook
            serie = f"{entity}{emission}"
        except:
             # Fallback for now or use fields from journal extension
             # In real implementation, use l10n_ec_entity from `account.journal`
             serie = f"{record.journal_id.l10n_ec_entity}{record.journal_id.l10n_ec_emission}"

        sequential = f"{record.name.split('-')[-1]:0>9}" # Extract sequence number

        # Random 8 digits
        code_numeric = f"{random.randint(1, 99999999):08d}"
        emission_type = '1' # Normal

        # 2. Construction (Pre-Verifier)
        base_key = f"{date_inv}{doc_type}{ruc}{env}{serie}{sequential}{code_numeric}{emission_type}"

        # 3. Check Digit (Modulo 11)
        verifier = self._get_modulo_11(base_key)

        access_key = f"{base_key}{verifier}"

        if len(access_key) != 49:
            raise ValidationError(f"Generated Access Key length is {len(access_key)}, expected 49.")

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

    @api.model
    def render_xml(self, record):
        """
        Render the XML using QWeb template.
        """
        # We assume a qweb template 'l10n_ec_sri.xml_invoice' exists
        # This returns bytes
        # In a real implementation, we pass formatted values
        values = {
            'record': record,
            'access_key': record.l10n_ec_sri_access_key,
            # Add all other XSD 2.26 fields here
        }
        return self.env['ir.qweb']._render('l10n_ec_sri.xml_invoice', values)
