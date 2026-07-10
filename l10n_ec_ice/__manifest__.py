# -*- coding: utf-8 -*-
{
    "name": "Ecuador - ICE (Impuesto Consumos Especiales)",
    "version": "1.2.0",
    "category": "Accounting/Localizations",
    "summary": "Manage specific and ad valorem ICE taxes",
    "description": """
        Implements LORTI Title III (Art. 75-89) for ICE.
        Supports:
        - Specific Rates (e.g. Cigarettes, Bags)
        - Specific Rates with Content (Alcohol, Sugar)
        - Ad Valorem Rates (Perfumes, Vehicles)

        --------------------------------------------------------------------
        Estado real (fork egejo/odoo_saas_ecuador, ver README.md del fork)
        --------------------------------------------------------------------
        Auditado y corregido 2026-07-10: la version original de este modulo
        NUNCA calculo el ICE en absoluto. Dependia de amount_type='code' y
        de un override de account.tax._compute_amount -- ninguno de los dos
        existe en el motor de impuestos de Odoo 18 (amount_type solo admite
        group/fixed/percent/division; el calculo real pasa por
        _eval_tax_amount_fixed_amount/_eval_tax_amount_price_included/
        _eval_tax_amount_price_excluded). Confirmado en vivo: crear un
        account.tax con amount_type='code' revienta con
        ValueError("Wrong value for account.tax.amount_type: 'code'") --
        nadie pudo haber configurado esto nunca, ni siquiera por error (0
        taxes/productos con categoria ICE existian en produccion). Se
        reescribio para enganchar los hooks reales del motor: 'specific' y
        'ad_valorem' ahora usan directamente amount_type nativo
        fixed/percent (sincronizado desde la categoria SRI, sin logica
        propia); solo 'specific_content' (alcohol/azucar, que depende de un
        factor por producto) necesita un override real, sobre
        _eval_tax_amount_fixed_amount. Verificado con los 5 tests del
        modulo (los 3 tipos de tarifa + la sincronizacion categoria->tax)
        corriendo de verdad contra la base de produccion via --test-enable
        (TransactionCase revierte cada test, no dejo datos). Tarifas
        especificas tambien actualizadas a la Resolucion NAC-DGERCGC25-
        00000040 (vigente desde 2026-01-01): alcohol 10.30->10.41,
        cerveza industrial 13.48->13.62, cerveza artesanal 1.54->1.56.
        Cigarrillos/fundas/bebidas azucaradas sin cambio.

        Escalonamiento real de Vehiculos Motorizados por PVP, 2026-07-10:
        el codigo "3092 Vehiculos Motorizados" (15% ad valorem plano)
        tenia DOS problemas reales, no uno: (1) el ICE de vehiculos no es
        un porcentaje unico, varia por tramo de PVP (Precio de Venta al
        Publico) segun la Tabla 18 del SRI (5% a 35%); (2) el codigo 3092
        en si mismo es el codigo SRI EQUIVOCADO -- 3092 corresponde
        oficialmente a "Servicios de Television Prepagada" (0%), sin
        ninguna relacion con vehiculos. Reemplazado por 7 tramos reales,
        cada uno su propia categoria/tax (mismo patron que cualquier
        otro codigo de este catalogo -- no requirio cambios en el motor
        de calculo ni en la generacion XML). Se agrego
        l10n_ec.ice.category.get_vehicle_bracket() para resolver el
        tramo correcto segun el PVP real del vehiculo (y si es
        camioneta/vehiculo de rescate, que tiene un tramo preferencial
        propio solo hasta USD 30.000), mas un onchange en
        product.template que auto-sugiere la categoria correcta a
        partir de l10n_ec_pvp. Cubierto por 17 tests. Confirmado
        AUTORIZADO contra el SRI real el mismo dia (tramo general y
        tramo camioneta/rescate). Migracion post-* incluida para limpiar
        el codigo 3092 huerfano.

        Auditoria de Perfumes/Videojuegos/Armas, 2026-07-10 (mismo dia,
        a peticion explicita del usuario -- cierra la nota que este
        mismo fix habia dejado sin confirmar mas arriba): confirmado
        contra 2 fuentes oficiales del SRI independientes (la Ficha
        Tecnica, seccion "TABLA 18: TARIFA DEL ICE", y el catalogo
        dedicado CATALOGO_ANEXO_ICE.xls descargado de sri.gob.ec, hoja
        "TABLA 7: CODIGOS DE IMPUESTO") que los 3 codigos de este
        catalogo estaban mal desde el dia 1, y que el fix de vehiculos
        de este mismo dia (parrafo anterior) tambien tenia 2 codigos de
        tramo equivocados por el mismo motivo:
        - Perfumes y Aguas de Tocador: codigo real 3610 (no 3072 -- 3072
          es en realidad "Camionetas y Furgones PVP hasta USD 30.000",
          un tramo de vehiculos). Tarifa 20% sin cambio.
        - Videojuegos: codigo real 3620 (no 3650, que no es un codigo
          SRI real). Tarifa real 0% (no 35% -- ambas fuentes oficiales
          coinciden, sin cambios entre 2023 y hoy).
        - Armas de Fuego, Armas Deportivas y Municiones: codigo real
          3630 (no 3610, que es Perfumes). Tarifa dejada en 30%
          (Decreto Ejecutivo 302, vigente desde jul-2024) pero
          **historicamente muy volatil** -- 300%->30%(ene-2023)->
          300%(fallo judicial Corte Pichincha, may-2024)->30%(Decreto
          302, jul-2024), sin confirmacion de que siga en 30% en 2026;
          el nombre del registro advierte verificar el decreto vigente
          antes de facturar un arma real.
        - Tramos de vehiculo del fix anterior, corregidos de paso:
          "camionetas/rescate hasta 30k" es codigo 3072 (no 3684, que
          no es un codigo SRI real) y "vehiculo excepto camioneta 20k-
          30k" es codigo 3074 (no 3686, tampoco real). Sin cambio de
          tarifa (5%/10%), ni de logica (get_vehicle_bracket no
          referencia codigos, solo vehicle_subtype/pvp_min/pvp_max).

        Sin re-probar contra el SRI real con los codigos corregidos
        (los tests de AUTORIZADO del mismo dia para vehiculos/perfumes
        usaron los codigos viejos, ahora sabidos incorrectos).
    """,
    "author": "Somatech Ecuador, egejo (fork: motor de calculo corregido y probado 2026-07-10, ver descripción)",
    "depends": ["account", "l10n_ec_base", "product"],
    "data": [
        "security/ir.model.access.csv",
        "data/l10n_ec.ice.category.csv",
        "views/l10n_ec_ice_category_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
