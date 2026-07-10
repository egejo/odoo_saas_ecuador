# -*- coding: utf-8 -*-
{
    "name": "Ecuador - ICE (Impuesto Consumos Especiales)",
    "version": "1.0",
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
        Cigarrillos/fundas/bebidas azucaradas sin cambio. Pendiente:
        Vehiculos Motorizados sigue modelado como un 15% ad valorem plano
        -- la tarifa real del SRI es escalonada por rango de precio de
        venta (Art. 82 LORTI), no un porcentaje unico; no se implemento el
        escalonamiento completo. Sin probar con un producto real ni contra
        el SRI (no hay documento SRI que declare ICE fuera de EDI de
        factura, que ya esta cubierto por l10n_ec_edi/l10n_ec_sri).
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
