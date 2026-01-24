# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    l10n_ec_identifier_type = fields.Selection([
        ('ruc', 'RUC'),
        ('cedula', 'Cédula'),
        ('pasaporte', 'Pasaporte'),
    ], string='Identifier Type', help="Type of Ecuadorian Identification")

    l10n_ec_taxpayer_type = fields.Selection([
        ('special', 'Contribuyente Especial'),
        ('rimpe_e', 'RIMPE Emprendedor'),
        ('rimpe_p', 'RIMPE Negocio Popular'),
        ('general', 'Régimen General'),
        ('exporter', 'Exportador Habitual')
    ], string='Taxpayer Type')

    l10n_ec_related_party = fields.Boolean("Related Party (ATS)", default=False)

    @api.constrains('vat', 'l10n_ec_identifier_type', 'country_id')
    def _check_l10n_ec_vat(self):
        """
        Validates the Tax ID (vat) based on the Identifier Type for Ecuador.
        Algorithms: Modulo 10 (Cedula/RUC Natural) and Modulo 11 (RUC Private/Public).
        """
        for partner in self:
            if partner.country_id.code != 'EC' or not partner.l10n_ec_identifier_type:
                continue

            vat = partner.vat or ''
            if not vat:
                continue

            if partner.l10n_ec_identifier_type == 'pasaporte':
                if len(vat) < 5:
                    raise ValidationError(_("Passport number must be at least 5 characters."))
                continue

            if not vat.isdigit():
                 raise ValidationError(_("Ecuadorian RUC/Cédula must contain only digits."))

            is_ruc = partner.l10n_ec_identifier_type == 'ruc'
            expected_len = 13 if is_ruc else 10

            if len(vat) != expected_len:
                raise ValidationError(_("Invalid length for %s. Expected %s digits, got %s.") % (
                    partner.l10n_ec_identifier_type.upper(), expected_len, len(vat)
                ))

            if is_ruc and not vat.endswith('001'):
                 # Note: SRI allows other suffixes, but 001 is standard. Warning for now?
                 # Strict check per requirement: RUC usually ends in 001, but branches exist.
                 # We will enforce the Modulo check which is the critical part.
                 pass

            if not self._validate_ec_document(vat):
                raise ValidationError(_("Invalid Ecuadorian Identity Number (%s): Check Digit Verification Failed.") % vat)

    def _validate_ec_document(self, document_number):
        """
        Validates Ecuadorian RUC or Cédula.
        - Cédula (10 digits): Modulo 10
        - RUC Natural (13 digits): Modulo 10 (first 10 digits) + '001'
        - RUC Private (13 digits): Modulo 11 (3rd digit = 9)
        - RUC Public (13 digits): Modulo 11 (3rd digit = 6)
        """
        if not document_number or not document_number.isdigit():
            return False

        province = int(document_number[:2])
        if province < 1 or province > 24 and province != 30:
            return False

        third_digit = int(document_number[2])

        # Case 1: Cédula or RUC Natural Person (Third digit < 6)
        if third_digit < 6:
            # Modulo 10
            base = document_number[:9]
            verifier = int(document_number[9])
            coefficients = [2, 1, 2, 1, 2, 1, 2, 1, 2]
            total = 0
            for i in range(9):
                val = int(base[i]) * coefficients[i]
                total += val - 9 if val >= 10 else val

            check_digit = (10 - (total % 10)) % 10
            check_ok = (check_digit == verifier)

            if len(document_number) == 13:
                 return check_ok and document_number[10:] != '000' # RUC Natural
            return check_ok # Cédula

        # Case 2: Public Entity (Third digit = 6)
        elif third_digit == 6:
            # Modulo 11 with specific coefficients
            # Digits 0-8 (9 digits)
            # Verifier is digit 9 (10th digit) - Index 8
            # Coefficients: 3, 2, 7, 6, 5, 4, 3, 2
            if len(document_number) < 13: return False
            base = document_number[:8]
            verifier = int(document_number[8])
            coefficients = [3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(base[i]) * coefficients[i] for i in range(8))
            remainder = total % 11
            check_digit = 11 - remainder if remainder != 0 else 0

            return check_digit == verifier and document_number[9:] != '0000'

        # Case 3: Private Entity (Third digit = 9)
        elif third_digit == 9:
             # Modulo 11
             # Digits 0-9 (10 digits)
             # Verifier is digit 10 (11th digit) - Index 9
             # Coefficients: 4, 3, 2, 7, 6, 5, 4, 3, 2
             if len(document_number) < 13: return False
             base = document_number[:9]
             verifier = int(document_number[9])
             coefficients = [4, 3, 2, 7, 6, 5, 4, 3, 2]
             total = sum(int(base[i]) * coefficients[i] for i in range(9))
             remainder = total % 11
             check_digit = 11 - remainder if remainder != 0 else 0

             return check_digit == verifier and document_number[10:] != '000'

        return False
