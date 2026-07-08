# -*- coding: utf-8 -*-
def migrate(cr, version):
    """
    Corrige, en instalaciones donde l10n_ec_withholding ya estaba
    instalado, dos registros de data/retention_codes_2026.xml que tenian
    el codigo SRI equivocado desde el dia 1 de este fork (no por la
    Resolucion NAC-DGERCGC26-00000009, pero encontrado auditando el
    catalogo contra ella): "RIMPE Negocio Popular" tenia el codigo 332B
    (el codigo real de ese concepto es 332; 332B es "Compra de bienes
    inmuebles", un concepto distinto) y "RIMPE Emprendedor" tenia el
    codigo 343A (el codigo real es 343; 343A pasa a ser "Energia
    electrica" en la Resolucion, con su propio registro nuevo en el
    mismo archivo). Tambien corrige dos tarifas desactualizadas: 304 (8%
    -> 10%, unificado por la Resolucion) y 3440 (2.75% -> 3%).

    Corre como pre-migracion (antes de que se cargue
    data/retention_codes_2026.xml en este -u) por dos motivos: (1) ese
    archivo esta en noupdate=1, asi que un -u normal no aplica estos
    cambios sobre una instalacion ya existente (mismo mecanismo que el
    catalogo de paises SRI en l10n_ec_base, ver esa migracion para el
    detalle); (2) el archivo tambien agrega un registro NUEVO con codigo
    343A ("Energia Electrica"): si el registro viejo tax_ret_ir_343a
    todavia tiene codigo=343A cuando ese INSERT corre, choca contra la
    constraint unique(code, type) y aborta la carga del modulo. Se
    corrige por SQL directo, no ORM: en la etapa 'pre' el modelo de este
    mismo modulo todavia no esta registrado en el registry (probado:
    env['l10n_ec.withholding.tax'] tira KeyError aqui).

    Ninguno de los 4 registros corregidos aqui tenia uso real en
    produccion (account.retention.line count = 0, verificado antes de
    este fix), no hay riesgo de reclasificar retenciones ya emitidas.
    """
    cr.execute(
        """
        SELECT imd.name, imd.res_id
        FROM ir_model_data imd
        WHERE imd.module = 'l10n_ec_withholding'
          AND imd.name IN (
              'tax_ret_ir_332b', 'tax_ret_ir_343a',
              'tax_ret_ir_304', 'tax_ret_ir_3440'
          )
        """
    )
    res_ids = dict(cr.fetchall())

    fixes = {
        "tax_ret_ir_332b": (
            "code = %s, name = %s",
            ("332", "RIMPE Negocio Popular / Otras Compras No Sujetas a Retención (0%)"),
        ),
        "tax_ret_ir_343a": (
            "code = %s, name = %s",
            ("343", "RIMPE Emprendedor / Otras Retenciones 1% (1%)"),
        ),
        "tax_ret_ir_304": (
            "percentage = %s, name = %s",
            (10.0, "Servicios Predomina Intelecto (10%)"),
        ),
        "tax_ret_ir_3440": (
            "percentage = %s, name = %s",
            (3.0, "Otras Retenciones (3%)"),
        ),
    }
    for xml_name, (set_clause, params) in fixes.items():
        res_id = res_ids.get(xml_name)
        if res_id:
            cr.execute(
                "UPDATE l10n_ec_withholding_tax SET %s WHERE id = %%s" % set_clause,
                params + (res_id,),
            )
