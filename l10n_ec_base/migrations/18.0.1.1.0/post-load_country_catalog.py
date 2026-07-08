# -*- coding: utf-8 -*-
import csv

from odoo import SUPERUSER_ID, api
from odoo.modules.module import get_resource_path


def migrate(cr, version):
    """
    Backfill de res.country.l10n_ec_code_ats/l10n_ec_code_tax_haven
    (catalogo de paises del SRI, ver data/res.country.csv) en
    instalaciones donde l10n_ec_base ya estaba instalado antes de que
    este catalogo existiera.

    El loader estandar de datos de Odoo (usado tanto por CSV como XML)
    omite la escritura sobre un external id ya existente si ese registro
    esta marcado noupdate=True Y el modulo se esta actualizando (-u) en
    vez de instalando por primera vez (-i) -- los paises de 'base' estan
    noupdate por diseno (para no pisar personalizaciones), asi que
    data/res.country.csv nunca llega a aplicarse en un `-u l10n_ec_base`
    sobre una instalacion existente (silencioso, sin error). Si se
    escribe ademas la coincidencia va bien en la primera instalacion del
    modulo -- este script solo hace falta para el caso de actualizar una
    instalacion previa. Se escribe via ORM directo, que no esta sujeto a
    esa proteccion.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    csv_path = get_resource_path("l10n_ec_base", "data", "res.country.csv")
    with open(csv_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            country = env.ref(row["id"], raise_if_not_found=False)
            if not country:
                continue
            country.write(
                {
                    "l10n_ec_code_ats": row["l10n_ec_code_ats"] or False,
                    "l10n_ec_code_tax_haven": row["l10n_ec_code_tax_haven"] or False,
                }
            )
