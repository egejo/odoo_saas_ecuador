# -*- coding: utf-8 -*-
"""
Auditoria 2026-07-10 contra 2 fuentes oficiales del SRI independientes
(la Ficha Tecnica de Comprobantes Electronicos, seccion "TABLA 18:
TARIFA DEL ICE", y el catalogo dedicado CATALOGO_ANEXO_ICE.xls
descargado directamente de sri.gob.ec, hoja "TABLAS PRODUCTO" / "TABLA
7: CODIGOS DE IMPUESTO"): los codigos de Perfumes/Videojuegos/Armas de
este catalogo estaban mal desde el dia 1 del fork.

- Perfumes y Aguas de Tocador: codigo real 3610 (no 3072 -- 3072 es en
  realidad "Camionetas y Furgones PVP hasta USD 30.000", un tramo de
  vehiculos; ver el fix de vehiculos de este mismo dia, SHA 86c43f5,
  que por este mismo motivo tambien tenia 2 codigos de tramo
  equivocados: 3684/3686 en vez de los reales 3072/3074).
- Videojuegos: codigo real 3620 (no 3650, que no es un codigo SRI real
  en absoluto), tarifa real 0% (no 35% -- ambas fuentes oficiales
  coinciden en 0%, sin cambios entre enero y diciembre 2023).
- Armas de Fuego, Armas Deportivas y Municiones: codigo real 3630 (no
  3610, que en realidad es Perfumes). Tarifa: historicamente MUY volatil
  (300% -> 30% desde ene-2023 -> 300% de nuevo por fallo judicial de la
  Corte Provincial de Pichincha en may-2024 -> 30% de nuevo por Decreto
  Ejecutivo 302 desde jul-2024) -- se dejo en 30% (ultimo decreto
  confirmado encontrado), pero el nombre del registro advierte
  explicitamente que hay que verificar el decreto vigente antes de
  facturar un arma real.

data/l10n_ec.ice.category.csv reutiliza los xmlids ice_3610/ice_3072
(el codigo del registro no cambia, solo su contenido -- un "-u" normal
ya los actualiza en el lugar). Pero ice_3650 (Videojuegos), ice_3684 y
ice_3686 (los 2 tramos de vehiculo con codigo equivocado, ver 86c43f5)
ya no aparecen en el CSV con esos xmlids -- quedarian huerfanos sin
esta migracion (el loader de datos de Odoo nunca borra registros
huerfanos solo porque se quiten del CSV).

Verificado antes de escribir esta migracion: los 2 account.tax de
prueba en produccion que si llegaron a usar los codigos de vehiculo
equivocados (ice_3684/ice_3686, creados y probados contra el SRI real
el mismo dia) tienen ondelete='set null' hacia esta tabla (confirmado
por SQL: pg_constraint.confdeltype = 'n') -- borrar estos registros no
falla, solo deja esos 2 taxes de prueba con la categoria en blanco
(sin impacto real, eran solo datos de prueba sinteticos).
"""


def migrate(cr, version):
    for code in ("3650", "3684", "3686"):
        cr.execute(
            "DELETE FROM l10n_ec_ice_category WHERE code = %s",
            (code,),
        )
    for xmlid in ("ice_3650", "ice_3684", "ice_3686"):
        cr.execute(
            "DELETE FROM ir_model_data WHERE module = %s AND name = %s",
            ("l10n_ec_ice", xmlid),
        )
