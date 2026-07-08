# -*- coding: utf-8 -*-
def migrate(cr, version):
    """
    Corrige, en instalaciones donde l10n_ec_withholding ya estaba
    instalado, el registro "No Procede Retención IVA (0%)"
    (tax_ret_iva_9), que tenía el código SRI equivocado: código 9 en
    realidad corresponde a 10% de retención IVA en la tabla oficial del
    SRI (Tabla 21), no a 0% (el código correcto para 0% es 7). Verificado
    contra Enterprise l10n_ec_edi (account_move.py,
    L10N_EC_WITHHOLD_VAT_CODES) como referencia estructural.

    Corre como pre-migración por el mismo motivo que
    pre-fix_retention_codes_2026.py (18.0.1.1.0): data/retention_codes_2026.xml
    agrega en esta misma versión un registro NUEVO con código 9 (ahora
    correctamente "Retención IVA 10%"), así que hay que liberar ese
    código del registro viejo antes de que el INSERT del nuevo corra, o
    choca contra la constraint unique(code, type). SQL directo, no ORM
    (el modelo propio del módulo no está en el registry en la etapa
    'pre').

    Sin uso en producción (account.retention.line count = 0 para este
    registro, verificado antes del fix) — no hay riesgo de reclasificar
    retenciones ya emitidas.

    De paso corrige también el nombre (cosmético, sin cambio de código
    ni porcentaje) de tax_ret_iva_3, que menciona ahora "Liquidación de
    Compra" además de Profesionales/Arriendo (misma tabla oficial: código
    3/100% cubre los tres casos) — no se aplicaría solo, por el mismo
    noupdate.
    """
    cr.execute(
        """
        SELECT name, res_id FROM ir_model_data
        WHERE module = 'l10n_ec_withholding'
          AND name IN ('tax_ret_iva_9', 'tax_ret_iva_3')
        """
    )
    res_ids = dict(cr.fetchall())

    if res_ids.get("tax_ret_iva_9"):
        cr.execute(
            "UPDATE l10n_ec_withholding_tax SET code = %s WHERE id = %s",
            ("7", res_ids["tax_ret_iva_9"]),
        )
    if res_ids.get("tax_ret_iva_3"):
        cr.execute(
            "UPDATE l10n_ec_withholding_tax SET name = %s WHERE id = %s",
            (
                "Retención IVA 100% (Profesionales/Arriendo/Liquidación de Compra)",
                res_ids["tax_ret_iva_3"],
            ),
        )
