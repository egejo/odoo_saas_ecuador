# -*- coding: utf-8 -*-
from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _load_pos_data_domain(self, data):
        """Garantiza que el Cliente por Defecto (Consumidor Final) del POS
        siempre llegue al frontend, sin importar si ya aparece entre los
        partners "mas usados/recientes" que carga el core por defecto -- si
        no llega, la asignacion automatica en pos_sri.js (PosOrder.setup)
        no tiene con que resolver la relacion y el cliente queda vacio.
        """
        domain = super()._load_pos_data_domain(data)
        config_id = self.env["pos.config"].browse(
            data["pos.config"]["data"][0]["id"]
        )
        default_partner = config_id.l10n_ec_default_partner_id
        if default_partner and domain and domain[0][:2] == ("id", "in"):
            ids = set(domain[0][2])
            ids.add(default_partner.id)
            domain = [("id", "in", list(ids))]
        return domain
