# Software Requirements Specification (SRS)
## Ecuador Localization - Deep Implementation Details

**Document ID:** SRS-L10N-EC-DEEP-2026-001
**Version:** 2.0.0
**Date:** 2026-01-25
**Module:** l10n_ec_base
**Classification:** Technical

---

## 1. RESUMEN DE MÓDULOS

### 1.1 Archivos Implementados

| Archivo | Líneas | Modelos/Clases | Propósito |
|:--------|:-------|:---------------|:----------|
| `res_partner.py` | 355 | ResPartner | Validación RUC, UAF, SRI auto-load |
| `tax_calendar.py` | 265 | L10nEcTaxCalendar | Cálculo fechas vencimiento |
| `purchase_order.py` | 143 | PurchaseOrder, ResConfigSettings | Penalidades DE 045-2025 |
| `l10n_ec_sri_ruc_service.py` | 344 | L10nEcSriRucService | API REST SRI |
| `l10n_ec_config.py` | 280+ | L10nEcConfig, RetentionCode, TaxCode | Parámetros dinámicos |
| `l10n_ec_catalogs.py` | 260+ | 7 modelos catálogo | Catálogos SRI |

---

## 2. MODELO: res_partner.py (ResPartner)

### 2.1 Campos Ecuador

| Campo | Tipo | Selection Values | Descripción |
|:------|:-----|:-----------------|:------------|
| `l10n_ec_identifier_type` | Selection | ruc, cedula, pasaporte | Tipo documento |
| `l10n_ec_taxpayer_type` | Selection | special, rimpe_e, rimpe_p, general, exporter | Régimen tributario |
| `l10n_ec_related_party` | Boolean | - | Parte relacionada ATS |
| `l10n_ec_government_contractor` | Boolean | - | Contratista Estado |
| `l10n_ec_uaf_certificate` | Binary | - | Certificado UAF |
| `l10n_ec_uaf_certificate_expiry` | Date | - | Vencimiento UAF |
| `l10n_ec_uaf_valid` | Boolean (computed) | - | UAF vigente |

### 2.2 Algoritmo Validación RUC/Cédula

**CÉDULA (10 dígitos) - Módulo 10:**
```
Coeficientes: [2, 1, 2, 1, 2, 1, 2, 1, 2]
Suma productos (si >= 10, restar 9)
Dígito verificador = (10 - suma % 10) % 10
```

**RUC SOCIEDAD PRIVADA (3er dígito = 9) - Módulo 11:**
```
Coeficientes: [4, 3, 2, 7, 6, 5, 4, 3, 2]
check_digit = 11 - (suma % 11), si 0 entonces 0
```

**RUC SECTOR PÚBLICO (3er dígito = 6) - Módulo 11:**
```
Coeficientes: [3, 2, 7, 6, 5, 4, 3, 2]
Verificador en posición 9 (índice 8)
```

### 2.3 Auto-carga SRI (onchange vat)

**Campos auto-completados:**
- name ← razon_social
- company_registry ← nombre_comercial
- street ← direccion
- city ← canton
- phone ← telefono
- email ← email
- l10n_ec_taxpayer_type ← según regimen_rimpe/contribuyente_especial

---

## 3. MODELO: tax_calendar.py

### 3.1 Mapa Vencimientos por 9º Dígito

| 9º Dígito | Día | Contrib. Especial |
|:----------|:----|:------------------|
| 1 | 10 | 9 |
| 2 | 12 | 9 |
| 3 | 14 | 9 |
| 4 | 16 | 9 |
| 5 | 18 | 9 |
| 6 | 20 | 9 |
| 7 | 22 | 9 |
| 8 | 24 | 9 |
| 9 | 26 | 9 |
| 0 | 28 | 9 |

### 3.2 Tipos de Declaración

| Tipo | Mes Vencimiento |
|:-----|:----------------|
| iva | Mes siguiente |
| retenciones | Mes siguiente |
| ats | Mes siguiente |
| ir | Abril año siguiente |
| rdep | Enero-Feb año siguiente |

---

## 4. MODELO: purchase_order.py (DE 045-2025)

### 4.1 Cálculo Penalidad

```python
delay = (actual_delivery - expected).days
penalty = amount_total * (rate / 100) * delay
penalty = min(penalty, amount_total * cap / 100)
```

### 4.2 Validación UAF

Si partner.l10n_ec_government_contractor = True
Y partner.l10n_ec_uaf_valid = False
→ ValidationError (bloquea confirmación)

---

## 5. API SRI (l10n_ec_sri_ruc_service.py)

### 5.1 Endpoints

```
GET /obtenerPorNumerosRuc?ruc=XXXXXXXXXXXXX
GET /obtenerPorNumeroCedula?cedula=XXXXXXXXXX
GET /obtenerPorRazonSocial?razonSocial=NOMBRE
```

### 5.2 Mapeo Respuesta

| API SRI | Campo Odoo |
|:--------|:-----------|
| numeroRuc | ruc |
| razonSocial | razon_social |
| nombreComercial | nombre_comercial |
| estadoContribuyente | estado |
| obligadoContabilidad | obligado_contabilidad (bool) |
| contribuyenteEspecial | contribuyente_especial |
| regimenRimpe | regimen_rimpe |
| direccionMatriz | direccion |
| nombreProvincia | provincia |
| nombreCanton | canton |
| telefono1 | telefono |
| correo | email |

---

## 6. PARÁMETROS DINÁMICOS 2026

| Parámetro | Valor | Fuente |
|:----------|:------|:-------|
| SBU | 482.0 | MDT |
| IESS Personal | 9.45% | IESS |
| IESS Patronal | 11.15% | IESS |
| IESS SECAP | 0.5% | IESS |
| IESS IECE | 0.5% | IESS |
| Total Empleador | 12.15% | Computed |
| Techo IESS | 12,050 | 25 SBU |
| IVA General | 15.0% | SRI |
| Fondos Reserva | 8.33% | MDT |
| Canasta Básica | 808.95 | INEC |

---

## 7. CATÁLOGOS SRI

### 7.1 Formas de Pago (8 registros)
01, 15-21

### 7.2 Tipos Identificación (5 registros)
04-08

### 7.3 Sustentos Tributarios (11 registros)
00-10

### 7.4 Tipos Contribuyente (8 registros)
01-08 (incluye RIMPE)

### 7.5 Provincias (24 registros)
Con región Costa/Sierra/Oriente/Insular

---

## 8. TOTALES

| Componente | Cantidad |
|:-----------|:---------|
| Modelos Odoo | 14 |
| Campos | 45+ |
| Métodos | 25+ |
| Registros catálogo | 56 |
| Líneas código | 1,450+ |

---

**FIN DEL DOCUMENTO**
