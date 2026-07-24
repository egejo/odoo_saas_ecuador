# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = "res.partner"

    l10n_ec_identifier_type = fields.Selection(
        [
            ("ruc", "RUC"),
            ("cedula", "Cédula"),
            ("pasaporte", "Pasaporte"),
        ],
        string="Identifier Type",
        help="Type of Ecuadorian Identification",
    )

    # El default nativo de `l10n_latam_base` es "NIF" (it_vat), pero apenas
    # se ejecuta su onchange de pais (que corre siempre al abrir una ficha
    # nueva, aun con el pais vacio, porque cae a
    # `company.account_fiscal_country_id`) lo reemplaza por el tipo marcado
    # `is_vat` del pais -- que en Ecuador es el RUC. En el mostrador, y en
    # el POS que abre esta misma ficha, la enorme mayoria de los clientes
    # son personas naturales con cedula, y ademas la consulta al catastro
    # se hace por cedula; abrir siempre en RUC obligaba a corregir el tipo
    # en cada venta. Se fija Cedula como default para compañias
    # ecuatorianas (el onchange de pais de l10n_latam_base respeta este
    # valor porque ec_dni ya es del pais correcto, y sigue sustituyendolo
    # solo si el usuario cambia el pais del contacto).
    l10n_latam_identification_type_id = fields.Many2one(
        default=lambda self: self._l10n_ec_default_identification_type(),
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Deriva el tipo de identificacion del numero cuando quien crea el
        contacto no lo indica.

        Hace falta por el default de arriba: un contacto creado por codigo
        (el importador del XML del proveedor, un checkout, una sincronizacion)
        no ejecuta los onchange del formulario, asi que se quedaba con el
        default -- Cedula -- aunque trajera un RUC de 13 digitos, y la
        restriccion de `l10n_ec` (Cedula obliga a 10 digitos) hacia fallar la
        creacion entera. Si el llamador SI indica el tipo, se respeta tal
        cual: que un tipo explicito y un numero incoherente choquen contra la
        restriccion es el comportamiento correcto.
        """
        for vals in vals_list:
            if vals.get("l10n_latam_identification_type_id"):
                continue
            vat = str(vals.get("vat") or "").strip()
            if not vat.isdigit() or len(vat) not in (10, 13):
                continue
            id_type = self.env.ref(
                "l10n_ec.ec_ruc" if len(vat) == 13 else "l10n_ec.ec_dni",
                raise_if_not_found=False,
            )
            if id_type:
                vals["l10n_latam_identification_type_id"] = id_type.id
        return super().create(vals_list)

    @api.model
    def _l10n_ec_default_identification_type(self):
        company = self.env.company
        country = company.account_fiscal_country_id or company.country_id
        if country.code == "EC":
            id_type = self.env.ref("l10n_ec.ec_dni", raise_if_not_found=False)
            if id_type:
                return id_type
        return self.env.ref("l10n_latam_base.it_vat", raise_if_not_found=False)

    @api.onchange("l10n_latam_identification_type_id")
    def _onchange_l10n_latam_identification_type_id_ec(self):
        """
        Evita pedir el tipo de identificacion dos veces en el mismo
        formulario. l10n_latam_identification_type_id (campo nativo) es
        la fuente real que usan TODAS las rutas activas de EDI/
        retenciones/ATS (via _l10n_ec_get_identification_type());
        l10n_ec_identifier_type (campo propio de este fork, vocabulario
        reducido ruc/cedula/pasaporte, usado solo por el reporte ATS y
        por el exportador EDI legado) se mantenia totalmente
        desconectado del nativo -- el usuario tenia que fijarlo aparte a
        mano, y si no coincidian el XML transmitido podia terminar
        clasificando al contacto distinto de como se veia en pantalla.
        Se sincroniza automaticamente aqui en vez de pedirlo dos veces.
        """
        if self.country_id and self.country_id.code != "EC":
            return
        mapping = {
            "cedula": "cedula",
            "ruc": "ruc",
            "ec_passport": "pasaporte",
            "passport": "pasaporte",
            "foreign": "pasaporte",
        }
        ec_type = self._l10n_ec_get_identification_type()
        if ec_type in mapping:
            self.l10n_ec_identifier_type = mapping[ec_type]

    def _l10n_ec_get_identification_type(self):
        # EXTENDS l10n_ec
        """
        Bug real visto en produccion (STARLINK ECUADOR STAREC C.LTDA.,
        RUC 1793200738001, partner id 14 en Adrenasports): el metodo
        base de l10n_ec cae a 'foreign' apenas
        l10n_latam_identification_type_id no es exactamente uno de los
        pocos xmlids que reconoce (RUC/Cedula/Pasaporte EC, o Pasaporte/
        ID Extranjera/VAT genericos de l10n_latam_base) -- un contacto
        ecuatoriano real con un tipo de identificacion generico sin
        country_id propio (ej. "NIF", el default que Odoo asigna a
        muchas compañias si nadie lo cambia a mano) termina clasificado
        como 'foreign' aunque el partner.country_id sea Ecuador y su vat
        tenga exactamente la forma de un RUC real. Esa clasificacion
        incorrecta se propaga al XML de retenciones
        (tipoIdentificacionSujetoRetenido=08, "exterior"), que el SRI
        rechaza con "ERROR EN DIFERENCIAS" porque exige tambien
        tipoSujetoRetenido (campo que solo aplica -- y que este fork no
        implementa todavia -- para proveedores realmente extranjeros).
        Antes de aceptar 'foreign', si el partner es de Ecuador y su vat
        tiene la longitud de un RUC/cedula real, se reclasifica por
        forma en vez de asumir "exterior" a ciegas.
        """
        result = super()._l10n_ec_get_identification_type()
        if result != "foreign" or self.country_id.code != "EC":
            return result
        vat = (self.vat or "").strip()
        if not vat.isdigit():
            return result
        if len(vat) == 13:
            return "ruc"
        if len(vat) == 10:
            return "cedula"
        return result

    l10n_ec_taxpayer_type = fields.Selection(
        [
            ("special", "Contribuyente Especial"),
            ("rimpe_e", "RIMPE Emprendedor"),
            ("rimpe_p", "RIMPE Negocio Popular"),
            ("general", "Régimen General"),
            ("exporter", "Exportador Habitual"),
        ],
        string="Taxpayer Type",
    )

    l10n_ec_related_party = fields.Boolean("Related Party (ATS)", default=False)

    # =========================================================================
    # Birth Date and Age - Auto-compute Tercera Edad
    # =========================================================================
    l10n_ec_fecha_nacimiento = fields.Date(
        string="Fecha de Nacimiento",
        help="Fecha de nacimiento para calcular edad automáticamente",
    )
    l10n_ec_edad = fields.Integer(
        string="Edad",
        compute="_compute_edad",
        store=True,
        help="Edad calculada automáticamente desde fecha de nacimiento",
    )
    l10n_ec_tercera_edad = fields.Boolean(
        string="Tercera Edad",
        compute="_compute_tercera_edad",
        store=True,
        help="LORTI Art. 74: Se activa automáticamente si edad ≥ 65 años",
    )

    @api.depends("l10n_ec_fecha_nacimiento")
    def _compute_edad(self):
        """Computes age from birthdate."""
        from datetime import date
        today = date.today()
        for partner in self:
            if partner.l10n_ec_fecha_nacimiento:
                born = partner.l10n_ec_fecha_nacimiento
                age = today.year - born.year - (
                    (today.month, today.day) < (born.month, born.day)
                )
                partner.l10n_ec_edad = age
            else:
                partner.l10n_ec_edad = 0

    @api.depends("l10n_ec_edad", "company_type")
    def _compute_tercera_edad(self):
        """Auto-compute Tercera Edad: person with age >= 65."""
        for partner in self:
            # Only persons can be Tercera Edad, not companies
            if partner.company_type == "person" and partner.l10n_ec_edad >= 65:
                partner.l10n_ec_tercera_edad = True
            else:
                partner.l10n_ec_tercera_edad = False

    # =========================================================================
    # Ley Orgánica de Discapacidades Art. 78: IVA Refund
    # =========================================================================
    l10n_ec_discapacidad = fields.Boolean(
        string="Persona con Discapacidad",
        default=False,
        help="Persona con discapacidad calificada por CONADIS. "
             "Derecho a devolución de IVA según Ley de Discapacidades Art. 78.",
    )
    l10n_ec_discapacidad_porcentaje = fields.Integer(
        string="Porcentaje Discapacidad",
        help="Porcentaje de discapacidad según carnet CONADIS (30% mínimo para beneficios)",
    )
    l10n_ec_discapacidad_carnet = fields.Char(
        string="Nº Carnet CONADIS",
        help="Número de carnet del CONADIS",
    )

    # =========================================================================
    # Entity Type and Special Regimes
    # =========================================================================
    l10n_ec_entity_type = fields.Selection(
        [
            ("sa", "Sociedad Anónima (S.A.)"),
            ("cia_ltda", "Compañía Limitada (Cía. Ltda.)"),
            ("sas", "Sociedad por Acciones Simplificada (S.A.S.)"),
            ("ep", "Empresa Pública (E.P.)"),
            ("fundacion", "Fundación sin Fines de Lucro"),
            ("ong", "ONG / Organismo Internacional"),
            ("cooperativa", "Cooperativa"),
            ("zede", "ZEDE - Zona Especial"),
            ("persona", "Persona Natural"),
        ],
        string="Tipo de Entidad",
        help="Tipo de entidad jurídica para tratamiento tributario",
    )
    l10n_ec_nueva_empresa = fields.Boolean(
        string="Nueva Empresa",
        help="LORTI Art. 9.1 bis: Exoneración de IR por 3 años para nuevas empresas",
    )
    l10n_ec_fecha_constitucion = fields.Date(
        string="Fecha de Constitución",
        help="Fecha de constitución de la empresa",
    )
    l10n_ec_artesano_calificado = fields.Boolean(
        string="Artesano Calificado",
        help="LORTI Art. 56: IVA 0% en servicios de artesanos calificados por JNDA",
    )

    @api.constrains("l10n_ec_discapacidad", "l10n_ec_discapacidad_porcentaje")
    def _check_discapacidad(self):
        """Validates disability percentage if disability is marked."""
        for partner in self:
            if partner.l10n_ec_discapacidad:
                if not partner.l10n_ec_discapacidad_porcentaje:
                    raise ValidationError(
                        _("Debe ingresar el porcentaje de discapacidad (30-100%).")
                    )
                if partner.l10n_ec_discapacidad_porcentaje < 30:
                    raise ValidationError(
                        _("El porcentaje mínimo para beneficios tributarios es 30%.")
                    )

    # =========================================================================
    # DE 045-2025: UAF Certificate for Government Contractors
    # =========================================================================
    l10n_ec_uaf_certificate = fields.Binary(
        string="Certificado UAF",
        attachment=True,
        help="Certificado de la Unidad de Análisis Financiero (UAF). "
        "Requerido por DE 045-2025 para contratistas del Estado.",
    )
    l10n_ec_uaf_certificate_filename = fields.Char(string="UAF Filename")
    l10n_ec_uaf_certificate_date = fields.Date(
        string="Fecha Emisión UAF", help="Fecha de emisión del certificado UAF"
    )
    l10n_ec_uaf_certificate_expiry = fields.Date(
        string="Fecha Vencimiento UAF", help="Fecha de vencimiento del certificado UAF"
    )
    l10n_ec_uaf_valid = fields.Boolean(
        string="UAF Válido",
        compute="_compute_uaf_valid",
        store=True,
        help="Indica si el certificado UAF está vigente",
    )
    l10n_ec_government_contractor = fields.Boolean(
        string="Contratista del Estado",
        default=False,
        help="Marcar si es proveedor de entidades gubernamentales",
    )

    @api.depends("l10n_ec_uaf_certificate", "l10n_ec_uaf_certificate_expiry")
    def _compute_uaf_valid(self):
        """Computes if UAF certificate is valid (exists and not expired)."""
        from datetime import date

        today = date.today()
        for partner in self:
            partner.l10n_ec_uaf_valid = False
            if partner.l10n_ec_uaf_certificate:
                if partner.l10n_ec_uaf_certificate_expiry:
                    partner.l10n_ec_uaf_valid = (
                        partner.l10n_ec_uaf_certificate_expiry >= today
                    )
                else:
                    # Has certificate but no expiry = assume valid
                    partner.l10n_ec_uaf_valid = True

    @api.constrains("l10n_ec_government_contractor", "l10n_ec_uaf_certificate")
    def _check_uaf_required(self):
        """
        DE 045-2025: Government contractors MUST have valid UAF certificate.
        """
        for partner in self:
            if (
                partner.l10n_ec_government_contractor
                and not partner.l10n_ec_uaf_certificate
            ):
                raise ValidationError(
                    _(
                        "DE 045-2025: Contratistas del Estado deben tener un "
                        "Certificado UAF válido.\\n\\n"
                        "Proveedor: %s\\n"
                        "Por favor, adjunte el certificado UAF antes de continuar."
                    )
                    % partner.name
                )

    @api.constrains("vat", "l10n_ec_identifier_type", "country_id")
    def _check_l10n_ec_vat(self):
        """
        Validates the Tax ID (vat) based on the Identifier Type for Ecuador.
        Algorithms: Modulo 10 (Cedula/RUC Natural) and Modulo 11 (RUC Private/Public).
        """
        for partner in self:
            if partner.country_id.code != "EC" or not partner.l10n_ec_identifier_type:
                continue

            vat = partner.vat or ""
            if not vat:
                continue

            if partner.l10n_ec_identifier_type == "pasaporte":
                if len(vat) < 5:
                    raise ValidationError(
                        _("Passport number must be at least 5 characters.")
                    )
                continue

            if not vat.isdigit():
                raise ValidationError(
                    _("Ecuadorian RUC/Cédula must contain only digits.")
                )

            is_ruc = partner.l10n_ec_identifier_type == "ruc"
            expected_len = 13 if is_ruc else 10

            if len(vat) != expected_len:
                raise ValidationError(
                    _("Invalid length for %s. Expected %s digits, got %s.")
                    % (partner.l10n_ec_identifier_type.upper(), expected_len, len(vat))
                )

            if is_ruc and not vat.endswith("001"):
                # Note: SRI allows other suffixes, but 001 is standard. Warning for now?
                # Strict check per requirement: RUC usually ends in 001, but branches exist.
                # We will enforce the Modulo check which is the critical part.
                pass

            if not self._validate_ec_document(vat):
                # Bug real reportado en produccion: un RUC de empresa real
                # (1793200738001, STARLINK ECUADOR STAREC C.LTDA.) no supera
                # el modulo 11 "de libro" y esto bloqueaba crear/editar el
                # contacto. El propio modulo core l10n_ec (ver
                # l10n_ec/models/res_partner.py, campo
                # l10n_ec_vat_validation) NO bloquea por esta razon --
                # solo advierte, con el comentario explicito de que "SRI ha
                # declarado que esta validacion ya no es obligatoria para
                # algunos numeros de RUC/cedula". Se alinea este modulo al
                # mismo criterio: el digito verificador ya no bloquea el
                # guardado, solo queda registrado en el log. La validacion
                # de longitud/formato de arriba (que si detecta errores de
                # digitacion inequivocos) se mantiene.
                _logger.info(
                    "Identificación EC '%s' (%s) no supera el dígito "
                    "verificador estándar (módulo 10/11) -- no se bloquea "
                    "el guardado, el SRI no siempre lo exige.",
                    vat,
                    partner.l10n_ec_identifier_type,
                )

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
            check_ok = check_digit == verifier

            if len(document_number) == 13:
                return check_ok and document_number[10:] != "000"  # RUC Natural
            return check_ok  # Cédula

        # Case 2: Public Entity (Third digit = 6)
        elif third_digit == 6:
            # Modulo 11 with specific coefficients
            # Digits 0-8 (9 digits)
            # Verifier is digit 9 (10th digit) - Index 8
            # Coefficients: 3, 2, 7, 6, 5, 4, 3, 2
            if len(document_number) < 13:
                return False
            base = document_number[:8]
            verifier = int(document_number[8])
            coefficients = [3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(base[i]) * coefficients[i] for i in range(8))
            remainder = total % 11
            check_digit = 11 - remainder if remainder != 0 else 0

            return check_digit == verifier and document_number[9:] != "0000"

        # Case 3: Private Entity (Third digit = 9)
        elif third_digit == 9:
            # Modulo 11
            # Digits 0-9 (10 digits)
            # Verifier is digit 10 (11th digit) - Index 9
            # Coefficients: 4, 3, 2, 7, 6, 5, 4, 3, 2
            if len(document_number) < 13:
                return False
            base = document_number[:9]
            verifier = int(document_number[9])
            coefficients = [4, 3, 2, 7, 6, 5, 4, 3, 2]
            total = sum(int(base[i]) * coefficients[i] for i in range(9))
            remainder = total % 11
            check_digit = 11 - remainder if remainder != 0 else 0

            return check_digit == verifier and document_number[10:] != "000"

        return False

    # =========================================================================
    # SRI AUTO-LOAD: carga automatica de datos al ingresar cedula o RUC
    # =========================================================================
    #
    # Originalmente esto solo funcionaba con RUC (13 digitos): quien
    # ingresaba una cedula (10 digitos) -- el caso mas comun en el mostrador
    # y en el POS, donde casi todo cliente es persona natural -- tenia que
    # escribir el nombre a mano. Se extendio a cedula usando
    # `consultar_cedula`, que deriva el RUC de persona natural
    # (cedula + "001") porque el endpoint de cedula del SRI esta deprecado
    # (404). Limitacion conocida y esperada: una persona que nunca saco RUC
    # no figura en el catastro -- eso NO es un error, es el caso normal de
    # "escriba el nombre a mano".

    def _l10n_ec_sri_query(self, vat):
        """Consulta el catastro del SRI por cedula (10) o RUC (13).

        Devuelve `(kind, data)`:
          - `(None, None)`  el numero no tiene forma de cedula ni de RUC,
                            asi que no hay nada que consultar (pasaporte,
                            identificacion extranjera, numero incompleto).
          - `(kind, None)`  se consulto y el catastro no devolvio nada
                            (o el servicio fallo).
          - `(kind, dict)`  datos del contribuyente.

        Nunca propaga excepciones: capturar un contacto no puede caerse
        porque el SRI este fuera de linea o cambie su API.
        """
        vat = str(vat or "").strip()
        if not vat.isdigit() or len(vat) not in (10, 13):
            return None, None
        kind = "ruc" if len(vat) == 13 else "cedula"
        try:
            service = self.env["l10n_ec.sri.ruc.service"]
            result = (
                service.consultar_ruc(vat)
                if kind == "ruc"
                else service.consultar_cedula(vat)
            )
        except Exception as e:  # noqa: BLE001 - el flujo nunca se cae
            _logger.warning(f"Error al consultar el SRI para {vat}: {e}")
            return kind, None
        if not result.get("success"):
            _logger.info(
                f"{kind} {vat} sin resultado en el catastro del SRI: "
                f"{result.get('error')}"
            )
            return kind, None
        return kind, result.get("data") or {}

    # Campos que solo se completan si estan vacios cuando la carga es
    # automatica (el onchange): lo que el usuario ya escribio a mano manda.
    # Los demas describen la clasificacion tributaria del contribuyente, no
    # una preferencia del usuario, asi que siempre reflejan el catastro.
    _L10N_EC_SRI_SOFT_FIELDS = ("name", "street", "city", "phone", "email")

    def _l10n_ec_sri_values(self, kind, data):
        """Traduce la respuesta del catastro a valores de la ficha.

        Se separo de `_l10n_ec_apply_sri_data` para que el boton
        "Consultar datos" pueda pedir los valores por RPC y volcarlos en el
        formulario del navegador SIN guardar el contacto -- guardarlo es lo
        que hacia que el POS cerrara la ventana a mitad de la carga (el POS
        pasa un `onSave` que cierra el dialogo y devuelve el cliente en
        cuanto el registro se graba, ver `makeActionAwaitable`).
        """
        values = {}
        for field, key in (
            ("name", "razon_social"),
            ("street", "direccion"),
            ("city", "canton"),
            ("phone", "telefono"),
            ("email", "email"),
        ):
            if data.get(key):
                values[field] = data[key]
        if data.get("nombre_comercial"):
            values["company_registry"] = data["nombre_comercial"]

        # Tipo de identificacion: se fija por la forma del numero, en los
        # DOS campos, para no dejarlos peleados entre si (el propio del
        # fork y el nativo de l10n_latam, que es el que usan las rutas de
        # EDI/retenciones/ATS).
        values["l10n_ec_identifier_type"] = kind
        # Una cedula es, por definicion, una persona natural: Odoo abre
        # todo contacto nuevo como "Empresa" por defecto y sin esto quedaba
        # una persona guardada como compañia.
        if kind == "cedula":
            values["company_type"] = "person"
        id_type = self.env.ref(
            "l10n_ec.ec_ruc" if kind == "ruc" else "l10n_ec.ec_dni",
            raise_if_not_found=False,
        )
        if id_type:
            values["l10n_latam_identification_type_id"] = id_type

        # Tipo de contribuyente segun SRI
        regimen = (data.get("regimen_rimpe") or "").upper()
        if regimen:
            if "EMPRENDEDOR" in regimen:
                values["l10n_ec_taxpayer_type"] = "rimpe_e"
            elif "POPULAR" in regimen:
                values["l10n_ec_taxpayer_type"] = "rimpe_p"
        elif data.get("contribuyente_especial"):
            values["l10n_ec_taxpayer_type"] = "special"
        else:
            values["l10n_ec_taxpayer_type"] = "general"
        return values

    def _l10n_ec_apply_sri_data(self, kind, data, overwrite=False):
        """Vuelca en la ficha lo que devolvio el catastro.

        Con `overwrite=False` (el onchange) nunca pisa lo que el usuario ya
        escribio; con `overwrite=True` (el boton manual) si, porque ahi
        pedir la actualizacion es un acto explicito.
        """
        for field, value in self._l10n_ec_sri_values(kind, data).items():
            if field in self._L10N_EC_SRI_SOFT_FIELDS and not overwrite:
                # "/" es el marcador de "sin nombre todavia" que usa Odoo en
                # un contacto recien abierto: cuenta como vacio.
                if self[field] and self[field] != "/":
                    continue
            self[field] = value
        if not self.country_id:
            self.country_id = self.env.ref("base.ec")

    @api.onchange("vat")
    def _onchange_vat_load_sri(self):
        """
        Carga automáticamente los datos del contribuyente desde el SRI
        cuando se ingresa una cédula o un RUC de Ecuador.
        """
        if not self.vat:
            return

        # Solo para Ecuador o si no hay país definido
        if self.country_id and self.country_id.code != "EC":
            return

        vat = str(self.vat).strip()

        # Aqui habia un guard anti-repeticion que hacia
        # `self._sri_loaded_ruc = vat`. Eso es imposible en Odoo 18: los
        # recordsets definen __slots__, asi que la asignacion siempre
        # lanzaba AttributeError -- lo tapaba el `except Exception` que
        # envolvia todo el metodo. Nunca evito una sola consulta y, peor,
        # abortaba el metodo justo antes del aviso de "contribuyente no
        # activo", que por eso jamas se mostro. Se elimina: el onchange
        # solo dispara cuando `vat` cambia de verdad, asi que no hay
        # consulta repetida que evitar.
        kind, data = self._l10n_ec_sri_query(vat)
        if not data:
            # Ni pasaporte ni "no esta en el catastro" son un error: el
            # usuario simplemente escribe el nombre a mano.
            return

        self._l10n_ec_apply_sri_data(kind, data)

        # Advertir si no está ACTIVO
        estado = (data.get("estado") or "").upper()
        if estado and estado != "ACTIVO":
            return {
                "warning": {
                    "title": "⚠️ Contribuyente No Activo",
                    "message": f"El contribuyente '{data.get('razon_social')}' tiene estado: {estado}. "
                    f"Verifique en el SRI antes de continuar.",
                }
            }

    @api.model
    def l10n_ec_sri_lookup(self, vat, country_id=None):
        """Consulta el catastro y DEVUELVE los valores, sin tocar la ficha.

        Lo llama el boton "Consultar datos" desde el navegador (widget
        `l10n_ec_sri_lookup`) para volcar el resultado en el formulario
        abierto. Deliberadamente no escribe ni guarda nada: el boton
        anterior era un `type="object"`, y en Odoo cualquier boton de ese
        tipo graba el registro antes de ejecutarse -- en el POS eso
        disparaba el `onSave` con el que abre la ficha (`makeActionAwaitable`
        de `pos_store`), que cierra el dialogo y devuelve el cliente a la
        orden, dejando al cajero sin poder completar correo/direccion.

        Devuelve siempre un dict serializable (nunca lanza), con:
          `ok`      si hubo datos para volcar,
          `values`  cambios listos para el formulario (m2o como [id, nombre]),
          `message` texto para la notificacion,
          `title`   titulo de la notificacion,
          `type`    success / warning.
        """
        vat = str(vat or "").strip()
        if not vat:
            return {
                "ok": False,
                "type": "warning",
                "title": "Falta la identificación",
                "message": "Ingrese la cédula o el RUC del contacto para "
                "consultarlo.",
            }

        kind, data = self._l10n_ec_sri_query(vat)
        if kind is None:
            return {
                "ok": False,
                "type": "warning",
                "title": "No se puede consultar",
                "message": f"El número '{vat}' no tiene forma de cédula (10 "
                "dígitos) ni de RUC (13 dígitos). Ingrese los datos a mano.",
            }
        if not data:
            return {
                "ok": False,
                "type": "warning",
                "title": "Sin resultados en el SRI",
                "message": f"No se encontró {'el RUC' if kind == 'ruc' else 'la cédula'} "
                f"{vat} en el catastro del SRI. Puede que el contacto nunca "
                "haya tenido RUC: ingrese los datos a mano.",
            }

        values = self._l10n_ec_sri_values(kind, data)
        # El formulario del navegador espera los many2one como
        # [id, nombre] (ver `_completeMany2OneValue` del modelo relacional).
        id_type = values.get("l10n_latam_identification_type_id")
        if id_type:
            values["l10n_latam_identification_type_id"] = [
                id_type.id,
                id_type.display_name,
            ]
        if not country_id:
            ecuador = self.env.ref("base.ec", raise_if_not_found=False)
            if ecuador:
                values["country_id"] = [ecuador.id, ecuador.display_name]

        estado = (data.get("estado") or "").upper()
        if estado and estado != "ACTIVO":
            return {
                "ok": True,
                "values": values,
                "type": "warning",
                "title": "⚠️ Contribuyente no activo",
                "message": f"{data.get('razon_social')} tiene estado {estado} "
                "en el SRI. Verifique antes de facturar.",
            }
        return {
            "ok": True,
            "values": values,
            "type": "success",
            "title": "Datos cargados",
            "message": data.get("razon_social") or "",
        }

    def action_load_from_sri(self):
        """
        Acción para cargar/actualizar datos desde el SRI manualmente.
        Invocable desde el botón de la ficha de contacto.
        """
        self.ensure_one()

        if not self.vat:
            raise ValidationError(
                _("Ingrese la cédula o el RUC del contacto para consultarlo.")
            )

        vat = str(self.vat).strip()
        kind, data = self._l10n_ec_sri_query(vat)
        if kind is None:
            raise ValidationError(
                _(
                    "El número '%s' no tiene forma de cédula (10 dígitos) ni "
                    "de RUC (13 dígitos), así que no se puede consultar. "
                    "Ingrese los datos a mano.",
                    vat,
                )
            )
        if not data:
            raise ValidationError(
                _(
                    "No se encontró %(kind)s %(vat)s en el catastro del SRI. "
                    "Puede que el contacto nunca haya tenido RUC: ingrese los "
                    "datos a mano.",
                    kind="el RUC" if kind == "ruc" else "la cédula",
                    vat=vat,
                )
            )

        # El botón es una petición explícita de actualizar, así que aquí sí
        # se sobrescribe lo que ya estaba en la ficha.
        self._l10n_ec_apply_sri_data(kind, data, overwrite=True)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "✅ Datos Cargados del SRI",
                "message": f"Contribuyente: {data.get('razon_social')}\n"
                f"Estado: {data.get('estado')}\n"
                f"Tipo: {data.get('tipo_contribuyente')}",
                "type": "success",
                "sticky": False,
            },
        }
