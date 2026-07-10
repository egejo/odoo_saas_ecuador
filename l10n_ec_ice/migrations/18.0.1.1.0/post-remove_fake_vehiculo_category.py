# -*- coding: utf-8 -*-
"""
El codigo 3092 se uso desde el dia 1 de este fork para "Vehiculos
Motorizados" (15% ad valorem plano) -- pero 3092 es en realidad el
codigo SRI oficial de "Servicios de Television Prepagada" (0%), sin
ninguna relacion con vehiculos. Se reemplazo por los tramos reales de
PVP (Tabla 18 del SRI): 3073/3686/3684/3075/3077/3078/3079/3080, ya
cargados via el CSV actualizado de este mismo commit.

data/l10n_ec.ice.category.csv no tiene noupdate=True (confirmado por
SQL antes de este fix), asi que un "-u" normal ya deja de re-crear el
registro viejo -- pero no lo borra solo por quitarlo del CSV, el
loader de Odoo nunca elimina registros huerfanos automaticamente. Se
borra aqui explicitamente porque, a diferencia de otros catalogos ya
migrados en este fork (paises, codigos de retencion), no hay ningun
registro NUEVO reusando el mismo codigo/xmlid con el que pudiera
chocar -- migracion post- simple, sin necesidad de SQL crudo.

Verificado antes de escribir esta migracion: 0 account.tax y 0
product.template referencian esta categoria en produccion, ningun
riesgo de dejar una referencia rota.
"""


def migrate(cr, version):
    cr.execute(
        "DELETE FROM l10n_ec_ice_category WHERE code = %s",
        ("3092",),
    )
    cr.execute(
        "DELETE FROM ir_model_data WHERE module = %s AND name = %s",
        ("l10n_ec_ice", "ice_3092"),
    )
