# Software Requirements Specification (SRS)
## Company Setup Wizard - Ecuador Localization

**Document ID:** SRS-WIZARD-EC-2026-001
**Version:** 1.0.0
**Date:** 2026-01-25
**Module:** l10n_ec / l10n_ec_base
**Classification:** Internal

---

## 1. RESUMEN EJECUTIVO

### 1.1 Propósito
Documentar el flujo completo del Wizard de Configuración de Empresa Ecuador, incluyendo la integración automática con el API REST del SRI para auto-completar datos del contribuyente.

### 1.2 Alcance
- Consulta automática de RUC en base de datos SRI
- Auto-llenado de campos desde respuesta API
- Validación de estado del contribuyente
- Mapeo a modelo `res.company` de Odoo

---

## 2. API SRI - ESPECIFICACIÓN TÉCNICA

### 2.1 Endpoints Disponibles

| Endpoint | Método | Parámetro | Descripción |
|:---------|:-------|:----------|:------------|
| `/obtenerPorNumerosRuc` | GET | `ruc` | Consulta por RUC (13 dígitos) |
| `/obtenerPorNumeroCedula` | GET | `cedula` | Consulta por cédula (10 dígitos) |
| `/obtenerPorRazonSocial` | GET | `razonSocial` | Búsqueda por nombre |

### 2.2 URL Base
```
https://srienlinea.sri.gob.ec/sri-catastro-sujeto-servicio-internet/rest/ConsolidadoContribuyente/
```

### 2.3 Headers Requeridos
```http
Accept: application/json
User-Agent: Odoo/18.0 SomatechEC/1.0
```

### 2.4 Ejemplo Request/Response

**Request:**
```
GET /obtenerPorNumerosRuc?ruc=1790016919001
```

**Response (200 OK):**
```json
[{
  "numeroRuc": "1790016919001",
  "razonSocial": "EMPRESA EJEMPLO S.A.",
  "nombreComercial": "EMPRESA EJEMPLO",
  "estadoContribuyente": "ACTIVO",
  "claseContribuyente": "ESPECIAL",
  "tipoContribuyente": "SOCIEDAD",
  "obligadoContabilidad": "SI",
  "actividadEconomicaPrincipal": "COMERCIO AL POR MAYOR",
  "codigoActividadEconomica": "G4610",
  "direccionMatriz": "AV. AMAZONAS 1234 Y NACIONES UNIDAS",
  "nombreCalle": "AV. AMAZONAS",
  "numeroCasa": "1234",
  "interseccion": "NACIONES UNIDAS",
  "nombreProvincia": "PICHINCHA",
  "nombreCanton": "QUITO",
  "nombreParroquia": "IÑAQUITO",
  "telefono1": "022567890",
  "correo": "info@empresa.com.ec",
  "fechaInicioActividades": "2010-01-15",
  "fechaActualizacion": "2025-12-01",
  "contribuyenteEspecial": "5368",
  "agenteRetencion": "123",
  "regimenRimpe": ""
}]
```

---

## 3. FLUJO DE PANTALLAS

### 3.1 Diagrama de Flujo

```
┌─────────────────────────────────────────────────────────────────┐
│                    INICIO WIZARD                                │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 1: INGRESO RUC                                            │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ RUC: [________________] ← Usuario ingresa 13 dígitos        ││
│  │                         ↓                                    ││
│  │                    onchange()                                ││
│  │                         ↓                                    ││
│  │              ┌─────────────────────┐                        ││
│  │              │ API SRI consultar_ruc│                       ││
│  │              └──────────┬──────────┘                        ││
│  │                         ↓                                    ││
│  │              ┌─────────────────────┐                        ││
│  │              │ Auto-llenar campos  │                        ││
│  │              └─────────────────────┘                        ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 2: DATOS CARGADOS (Editable)                              │
│  ┌───────────────────┬─────────────────────────────────────────┐│
│  │ Razón Social:     │ [AUTO: razonSocial]                     ││
│  │ Nombre Comercial: │ [AUTO: nombreComercial]                 ││
│  │ Estado SRI:       │ [AUTO: estadoContribuyente] ✅          ││
│  │ Tipo Contribuy:   │ [AUTO: tipoContribuyente]               ││
│  │ Clase Contribuy:  │ [AUTO: claseContribuyente]              ││
│  │ Actividad Econ:   │ [AUTO: actividadEconomicaPrincipal]     ││
│  │ Obligado Contab:  │ [AUTO: obligadoContabilidad] ☑          ││
│  │ Contrib. Especial:│ [AUTO: contribuyenteEspecial]           ││
│  │ Agente Retención: │ [AUTO: agenteRetencion]                 ││
│  │ Régimen RIMPE:    │ [AUTO: regimenRimpe]                    ││
│  └───────────────────┴─────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 3: DIRECCIÓN (Editable)                                   │
│  ┌───────────────────┬─────────────────────────────────────────┐│
│  │ Dirección:        │ [AUTO: direccionMatriz]                 ││
│  │ Ciudad:           │ [AUTO: nombreCanton]                    ││
│  │ Provincia:        │ [AUTO: nombreProvincia]                 ││
│  │ Teléfono:         │ [AUTO: telefono1]                       ││
│  │ Email:            │ [AUTO: correo]                          ││
│  └───────────────────┴─────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  PASO 4: CONFIGURACIÓN SRI                                      │
│  ┌───────────────────┬─────────────────────────────────────────┐│
│  │ Ambiente SRI:     │ ○ Pruebas  ◉ Producción                 ││
│  └───────────────────┴─────────────────────────────────────────┘│
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│  [✅ Configurar Empresa] [Configurar Después]                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. MAPEO DE CAMPOS

### 4.1 API SRI → Wizard

| Campo API SRI | Tipo | Campo Wizard | Auto-fill |
|:--------------|:-----|:-------------|:----------|
| `numeroRuc` | string(13) | `company_ruc` | ❌ Input |
| `razonSocial` | string | `company_name` | ✅ AUTO |
| `nombreComercial` | string | `commercial_name` | ✅ AUTO |
| `estadoContribuyente` | string | `sri_estado` | ✅ AUTO |
| `tipoContribuyente` | string | `sri_tipo_contribuyente` | ✅ AUTO |
| `claseContribuyente` | string | `sri_clase_contribuyente` | ✅ AUTO |
| `actividadEconomicaPrincipal` | string | `sri_actividad` | ✅ AUTO |
| `obligadoContabilidad` | "SI"/"NO" | `obligado_contabilidad` | ✅ AUTO |
| `contribuyenteEspecial` | string | `contribuyente_especial` | ✅ AUTO |
| `agenteRetencion` | string | `agente_retencion` | ✅ AUTO |
| `regimenRimpe` | string | `regimen_rimpe` | ✅ AUTO |
| `direccionMatriz` | string | `street` | ✅ AUTO |
| `nombreCanton` | string | `city` | ✅ AUTO |
| `nombreProvincia` | string | `province` | ✅ AUTO |
| `telefono1` | string | `phone` | ✅ AUTO |
| `correo` | string | `email` | ✅ AUTO |

### 4.2 Wizard → res.company (Odoo)

| Campo Wizard | Campo res.company | Transformación |
|:-------------|:------------------|:---------------|
| `company_name` | `name` | Directo |
| `company_ruc` | `vat` | Directo |
| `commercial_name` | `company_registry` | Directo |
| `street` | `street` | Directo |
| `city` | `city` | Directo |
| `province` | `state_id` | Buscar en res.country.state |
| - | `country_id` | Fijo: Ecuador (base.ec) |
| `phone` | `phone` | Directo |
| `email` | `email` | Directo |
| `website` | `website` | Manual |

### 4.3 Wizard → ir.config_parameter

| Campo Wizard | Parámetro | Valor |
|:-------------|:----------|:------|
| `sri_environment` | `l10n_ec.sri_environment` | "test" / "production" |
| `obligado_contabilidad` | `l10n_ec.obligado_contabilidad` | "True" / "False" |
| `contribuyente_especial` | `l10n_ec.contribuyente_especial` | Número resolución |
| `agente_retencion` | `l10n_ec.agente_retencion` | Número resolución |

---

## 5. CAMPOS API SRI NO UTILIZADOS (Disponibles)

| Campo API | Uso Potencial | Prioridad |
|:----------|:--------------|:----------|
| `codigoActividadEconomica` | Clasificación CIIU | Alta |
| `nombreParroquia` | Dirección completa | Media |
| `nombreCalle` | Dirección detallada | Media |
| `numeroCasa` | Dirección detallada | Media |
| `interseccion` | Dirección detallada | Baja |
| `fechaInicioActividades` | Antigüedad empresa | Alta |
| `fechaActualizacion` | Auditoría | Baja |
| `estadoEstablecimiento` | Validación local | Media |

---

## 6. VALIDACIONES

### 6.1 Validación de Entrada

| Campo | Regla | Mensaje Error |
|:------|:------|:--------------|
| RUC | 13 dígitos numéricos | "El RUC debe tener 13 dígitos numéricos" |
| RUC | Algoritmo módulo 10/11 | "RUC inválido" |
| Estado | != "ACTIVO" | ⚠️ Warning: "Contribuyente no activo" |

### 6.2 Validación API

| Código HTTP | Acción |
|:------------|:-------|
| 200 | Procesar respuesta |
| 404 | "RUC no existe en la base del SRI" |
| 500 | "Error de conexión con SRI" |
| Timeout (15s) | "Tiempo de espera agotado" |

---

## 7. CÓDIGO IMPLEMENTACIÓN

### 7.1 Servicio SRI (l10n_ec_sri_ruc_service.py)

```python
# Modelo: l10n_ec.sri.ruc.service

def consultar_ruc(self, ruc):
    url = f"{SRI_RUC_ENDPOINT}?ruc={ruc}"
    response = requests.get(url, headers=headers, timeout=15)

    if response.status_code == 200:
        data = response.json()[0]
        return {
            'success': True,
            'data': self._parse_sri_response(data)
        }
```

### 7.2 Wizard onchange (l10n_ec_company_setup_wizard.py)

```python
@api.onchange("company_ruc")
def _onchange_company_ruc(self):
    if len(self.company_ruc) == 13:
        result = self.env["l10n_ec.sri.ruc.service"].consultar_ruc(ruc)
        if result["success"]:
            data = result["data"]
            self.company_name = data.get("razon_social")
            self.commercial_name = data.get("nombre_comercial")
            # ... resto de campos
```

---

## 8. ARCHIVOS RELACIONADOS

| Archivo | Propósito |
|:--------|:----------|
| `l10n_ec_base/models/l10n_ec_sri_ruc_service.py` | Servicio API SRI |
| `l10n_ec/wizard/l10n_ec_company_setup_wizard.py` | Lógica wizard |
| `l10n_ec/wizard/l10n_ec_company_setup_wizard_views.xml` | Vista XML |
| `l10n_ec/hooks.py` | Auto-ejecutar wizard post-install |

---

## 9. APROBACIONES

| Rol | Nombre | Fecha |
|:----|:-------|:------|
| Desarrollador | __________ | ______ |
| QA | __________ | ______ |
| Product Owner | __________ | ______ |

---

**FIN DEL DOCUMENTO SRS-WIZARD-EC-2026-001**
