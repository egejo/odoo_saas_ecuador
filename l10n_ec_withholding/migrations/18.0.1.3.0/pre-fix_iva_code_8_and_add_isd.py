# -*- coding: utf-8 -*-
def migrate(cr, version):
    """
    Corrige, en instalaciones donde l10n_ec_withholding ya estaba
    instalado, el código IVA del registro "No Procede Retención IVA
    (0%)" (tax_ret_iva_9): tenía código 7 desde la migración anterior
    (18.0.1.2.0/1), pero localizada la Ficha Técnica oficial del SRI
    (v2.26, marzo-2024, Tabla 20) resulta que 7 es "Retención en cero"
    (un caso puntual, Disposición Transitoria Única de la Resolución
    NAC-DGERCGC15-00000284) y 8 es "No procede retención" (el caso
    general, que es lo que este registro representa por nombre).
    Enterprise l10n_ec_edi (usado como referencia el 2026-07-08 antes de
    encontrar la Ficha Técnica) colapsa ambos casos en un único código 7,
    de ahí el error original.

    Corre como pre-migración por el mismo motivo de siempre: el archivo
    de datos agrega en esta misma versión un registro NUEVO con código 7
    (ahora correctamente "Retención en Cero IVA"), así que hay que
    liberar ese código del registro viejo antes de que el INSERT del
    nuevo corra. SQL directo (el modelo propio del módulo no está en el
    registry en la etapa 'pre').

    Sin uso en producción para este registro (account.retention.line
    count = 0, verificado antes del fix).

    (Esta migración no toca el catálogo ISD nuevo — ese es un registro
    completamente nuevo con un código, 4580, que no colisiona con nada
    existente, así que se crea solo con la carga normal de
    data/retention_codes_2026.xml en este mismo -u, sin necesitar ORM ni
    SQL aquí.)
    """
    cr.execute(
        """
        SELECT res_id FROM ir_model_data
        WHERE module = 'l10n_ec_withholding' AND name = 'tax_ret_iva_9'
        """
    )
    row = cr.fetchone()
    if row:
        cr.execute(
            "UPDATE l10n_ec_withholding_tax SET code = %s WHERE id = %s",
            ("8", row[0]),
        )
