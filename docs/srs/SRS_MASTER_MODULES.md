# SRS - MASTER MODULE REGISTRY
## Ecuador Localization - ALL Modules Map

**Document ID:** SRS-L10N-EC-MASTER-MODULES
**Version:** 1.0.0
**Date:** 2026-01-25
**Status:** PLANNING
**Goal:** THE BEST OPEN-SOURCE ERP FOR ECUADOR

---

## 1. MODULE REGISTRY - COMPLETE

| # | Odoo Module | Ecuador Module | Legal Base | Priority | SRS Doc |
|:--|:------------|:---------------|:-----------|:---------|:--------|
| 1 | account | l10n_ec_base | LORTI, NEC/NIIF | P1 | ✅ Done |
| 2 | account_edi | l10n_ec_edi | NAC-DGERCGC25-17 | P1 | Pending |
| 3 | sale | l10n_ec_sale | LORTI Art. 64 | P1 | Pending |
| 4 | purchase | l10n_ec_purchase | LORTI Art. 43-50 | P1 | Pending |
| 5 | stock | l10n_ec_stock | COPCI Art. 142 | P1 | ✅ Done |
| 6 | mrp | l10n_ec_mrp | RTE INEN | P2 | ✅ Done |
| 7 | hr | l10n_ec_hr | Código Trabajo | P1 | ✅ Done |
| 8 | hr_payroll | l10n_ec_hr_payroll | CT + IESS | P1 | ✅ Done |
| 9 | hr_holidays | l10n_ec_hr_holidays | CT Art. 69-78 | P1 | ✅ Done |
| 10 | hr_contract | l10n_ec_hr_contract | CT Art. 12-17 | P1 | ✅ Done |
| 11 | point_of_sale | l10n_ec_pos | NAC-DGERCGC25-17 | P1 | Pending |
| 12 | crm | l10n_ec_crm | LOPDP, ATS | P2 | **NEW** |
| 13 | project | l10n_ec_project | LORTI deducibles | P3 | **NEW** |
| 14 | fleet | l10n_ec_fleet | LOTTTSV | P2 | ✅ Done |
| 15 | maintenance | l10n_ec_maintenance | DE 255, SST | P3 | **NEW** |
| 16 | quality | l10n_ec_quality | ARCSA, INEN | P2 | ✅ Done |
| 17 | website_sale | l10n_ec_ecommerce | Ley Comercio Electr. | P2 | **NEW** |
| 18 | helpdesk | l10n_ec_helpdesk | LODC Art. 4 | P3 | **NEW** |
| 19 | documents | l10n_ec_documents | Archivo digital | P3 | **NEW** |
| 20 | sign | l10n_ec_sign | Ley Firma Electr. | P2 | **NEW** |
| 21 | l10n_ec_withholding | - | LORTI Art. 43-50 | P1 | ✅ Done |
| 22 | l10n_ec_reports | - | LORTI Art. 107 | P1 | **NEW** |
| 23 | l10n_ec_customs | - | COPCI Art. 108-216 | P1 | ✅ Done |
| 24 | l10n_ec_asset | - | LORTI Art. 28 | P2 | **NEW** |

---

## 2. CRM - Ecuador Specific

### 2.1 Legal Requirements

| Requirement | Law | Impact |
|:------------|:----|:-------|
| Protección datos personales | LOPDP 2021 | Consentimiento, derechos ARCO |
| Datos fiscales | LORTI | RUC/Cédula obligatorio |
| Comunicaciones comerciales | LODC Art. 4 | Opt-in/opt-out |
| Historial para ATS | SRI | Reportar transacciones |

### 2.2 CRM Extensions

```python
# Lead/Opportunity Fields
l10n_ec_ruc_opportunity = Char  # RUC prospecto
l10n_ec_sector_economico = Selection  # CIIU classification
l10n_ec_tipo_cliente_potencial = Selection([
    ('persona_natural', 'Persona Natural'),
    ('persona_juridica', 'Persona Jurídica'),
    ('gobierno', 'Sector Público'),
    ('exportador', 'Exportador'),
])
l10n_ec_presupuesto_anual = Float  # Budget estimation
l10n_ec_consentimiento_datos = Boolean  # LOPDP consent
l10n_ec_fecha_consentimiento = Date
```

### 2.3 CRM to Sale Flow

```
Lead → Opportunity → Quotation → Sale Order → Invoice
  │                                              │
  └── RUC validation ─────────────────────────→ Factura electrónica
```

---

## 3. SALES - Ecuador Specific

### 3.1 Sales Order Extensions

| Field | Purpose | Legal Base |
|:------|:--------|:-----------|
| l10n_ec_forma_pago | Payment method | ATS |
| l10n_ec_plazo_credito | Credit days | LORTI |
| l10n_ec_tipo_venta | Sale type | ATS |
| l10n_ec_punto_emision | Emission point | SRI |

### 3.2 Sales Flow

```
FLOW: Venta Completa Ecuador
┌─────────────────────────────────────────────────────────────┐
│ 1. COTIZACIÓN                                               │
│    ├── Validar cliente (RUC/Cédula)                        │
│    ├── Aplicar precios con IVA                             │
│    └── Definir forma de pago                               │
│                                                             │
│ 2. ORDEN DE VENTA                                           │
│    ├── Confirmar disponibilidad stock                      │
│    ├── Reservar inventario                                 │
│    └── Generar picking                                     │
│                                                             │
│ 3. ENTREGA                                                  │
│    ├── Preparar mercadería                                 │
│    ├── Emitir GUÍA DE REMISIÓN electrónica                │
│    ├── Autorización SRI                                    │
│    └── Entregar con RIDE                                   │
│                                                             │
│ 4. FACTURACIÓN                                              │
│    ├── Crear factura desde SO                              │
│    ├── Validar datos fiscales                              │
│    ├── Emitir FACTURA electrónica                         │
│    └── Autorización SRI                                    │
│                                                             │
│ 5. COBRO                                                    │
│    ├── Registrar pago                                       │
│    ├── Forma de pago para ATS                              │
│    └── Conciliar cuenta                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. PURCHASE - Ecuador Specific

### 4.1 Purchase Extensions

| Field | Purpose | Legal Base |
|:------|:--------|:-----------|
| l10n_ec_sustento_tributario | Tax support | ATS |
| l10n_ec_tipo_proveedor | Supplier type | Retenciones |
| l10n_ec_importacion | Is import | SENAE |

### 4.2 Purchase Flow with Retention

```
FLOW: Compra con Retención
┌─────────────────────────────────────────────────────────────┐
│ 1. SOLICITUD COMPRA                                         │
│    ├── Producto/Servicio                                   │
│    └── Proveedor validado                                  │
│                                                             │
│ 2. ORDEN DE COMPRA                                          │
│    ├── Términos de pago                                    │
│    ├── Tipo de gasto (código retención)                   │
│    └── Confirmar                                           │
│                                                             │
│ 3. RECEPCIÓN                                                │
│    ├── Recibir mercadería                                  │
│    ├── Verificar vs factura proveedor                      │
│    └── Registrar lotes si aplica                          │
│                                                             │
│ 4. FACTURA PROVEEDOR                                        │
│    ├── Ingresar factura electrónica                        │
│    ├── Validar clave acceso SRI                           │
│    ├── Calcular retenciones automáticas                   │
│    └── Generar RETENCIÓN electrónica                      │
│                                                             │
│ 5. PAGO                                                     │
│    ├── Pago neto (factura - retención)                    │
│    ├── Forma de pago para ATS                              │
│    └── ISD si pago al exterior                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. POS - Ecuador Specific

### 5.1 POS Requirements

| Requirement | Legal Base | Implementation |
|:------------|:-----------|:---------------|
| Factura electrónica | NAC-DGERCGC25-17 | Online mode |
| Nota de venta | ≤$50 | Simplified |
| Consumidor final | 9999999999999 | Default customer |
| Impresión RIDE | SRI | Thermal printer |

### 5.2 POS Flow

```
FLOW: Venta POS Ecuador
┌─────────────────────────────────────────────────────────────┐
│ 1. SESIÓN                                                   │
│    ├── Abrir caja                                           │
│    ├── Fondo inicial                                        │
│    └── Punto de emisión activo                             │
│                                                             │
│ 2. VENTA                                                    │
│    ├── Agregar productos                                    │
│    ├── Cliente (cédula opcional <$50)                      │
│    └── Calcular IVA 15%                                    │
│                                                             │
│ 3. PAGO                                                     │
│    ├── Efectivo, tarjeta, transferencia                    │
│    └── Código forma pago                                   │
│                                                             │
│ 4. DOCUMENTO                                                │
│    ├── Total ≤ $50: Nota de venta                         │
│    ├── Total > $50: Factura electrónica                   │
│    ├── Envío SRI                                           │
│    └── Imprimir RIDE                                       │
│                                                             │
│ 5. CIERRE                                                   │
│    ├── Arqueo de caja                                      │
│    ├── Cuadrar vs Z report                                 │
│    └── Resumen diario                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 6. E-COMMERCE - Ecuador Specific

### 6.1 E-Commerce Requirements

| Requirement | Law | Implementation |
|:------------|:----|:---------------|
| Derecho retracto | LODC Art. 46 | 15 días devolución |
| Info obligatoria | Ley Comercio Electr. | Razón social, RUC, dirección |
| Cookies consent | LOPDP | Banner obligatorio |
| Precio con IVA | LODC | Mostrar precio final |
| Factura electrónica | SRI | Al confirmar compra |

### 6.2 E-Commerce Flow

```
FLOW: Venta Online Ecuador
┌─────────────────────────────────────────────────────────────┐
│ 1. CHECKOUT                                                 │
│    ├── Solicitar cédula/RUC (opcional <$50)                │
│    ├── Dirección entrega (provincia → cantón)              │
│    └── Aceptar términos (LOPDP)                            │
│                                                             │
│ 2. PAGO                                                     │
│    ├── Tarjeta (3DS2 obligatorio)                          │
│    ├── Transferencia                                        │
│    ├── Payphone, etc.                                      │
│    └── Contra entrega                                      │
│                                                             │
│ 3. CONFIRMACIÓN                                             │
│    ├── Emitir factura electrónica                          │
│    ├── Enviar RIDE por email                               │
│    └── Generar guía remisión                               │
│                                                             │
│ 4. ENVÍO                                                    │
│    ├── Courier con tracking                                │
│    └── Guía remisión física                                │
│                                                             │
│ 5. POST-VENTA                                               │
│    ├── Derecho retracto 15 días                            │
│    ├── Nota crédito electrónica                            │
│    └── Devolución IVA                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. PROJECT - Ecuador Specific

### 7.1 Project Extensions

| Field | Purpose | Legal Base |
|:------|:--------|:-----------|
| l10n_ec_contrato_publico | Gov contract | LOSNCP |
| l10n_ec_numero_proceso | SERCOP number | LOSNCP |
| l10n_ec_garantias | Required guarantees | LOSNCP |
| l10n_ec_anticipos | Advance payments | LORTI |

### 7.2 Government Contract Flow

```
FLOW: Proyecto Contratación Pública
┌─────────────────────────────────────────────────────────────┐
│ 1. ADJUDICACIÓN                                             │
│    ├── Número proceso SERCOP                               │
│    ├── Contrato firmado                                    │
│    └── Garantías constituidas                              │
│                                                             │
│ 2. EJECUCIÓN                                                │
│    ├── Registro avance                                      │
│    ├── Actas entrega-recepción                             │
│    └── Planillas de pago                                   │
│                                                             │
│ 3. FACTURACIÓN                                              │
│    ├── Factura por planilla                                │
│    ├── Retención recibida de entidad                       │
│    └── IVA retenido 100%                                   │
│                                                             │
│ 4. LIQUIDACIÓN                                              │
│    ├── Acta recepción definitiva                           │
│    ├── Devolución garantías                                │
│    └── Informe final                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. ASSETS - Ecuador Specific

### 8.1 Depreciation (LORTI Art. 28)

| Asset Type | Annual Rate | Years | Method |
|:-----------|:------------|:------|:-------|
| Inmuebles | 5% | 20 | Línea recta |
| Maquinaria | 10% | 10 | Línea recta |
| Vehículos | 20% | 5 | Línea recta |
| Equipos cómputo | 33% | 3 | Línea recta |
| Muebles y enseres | 10% | 10 | Línea recta |
| Otros | 10% | 10 | Línea recta |

### 8.2 Asset Flow

```
FLOW: Activo Fijo Ecuador
┌─────────────────────────────────────────────────────────────┐
│ 1. ADQUISICIÓN                                              │
│    ├── Compra (factura electrónica)                        │
│    ├── Retención aplicada                                  │
│    └── Crear activo fijo                                   │
│                                                             │
│ 2. ALTA                                                     │
│    ├── Clasificar según LORTI                              │
│    ├── Definir vida útil                                   │
│    ├── Valor residual                                       │
│    └── Ubicación física                                    │
│                                                             │
│ 3. DEPRECIACIÓN MENSUAL                                     │
│    ├── Cálculo automático                                  │
│    ├── Asiento contable                                    │
│    └── Reporte para IR                                     │
│                                                             │
│ 4. BAJA/VENTA                                               │
│    ├── Reverso depreciación acumulada                      │
│    ├── Resultado (ganancia/pérdida)                        │
│    └── Si venta: factura electrónica                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. REPORTS - Ecuador Specific

### 9.1 Required Reports

| Report | Frequency | Recipient | Legal Base |
|:-------|:----------|:----------|:-----------|
| **ATS** | Mensual | SRI | LORTI Art. 107 |
| **Formulario 104** | Mensual | SRI | LORTI |
| **Formulario 103** | Mensual | SRI | LORTI |
| **Formulario 101/102** | Anual | SRI | LORTI |
| **Planilla IESS** | Mensual | IESS | Ley IESS |
| **Décimo Tercero** | Anual | MDT | CT Art. 111 |
| **Décimo Cuarto** | Anual | MDT | CT Art. 113 |
| **Utilidades** | Anual | MDT | CT Art. 97 |

### 9.2 ATS Structure

```
ATS (Anexo Transaccional Simplificado)
├── compras[]
│   ├── tipoIdentificacion
│   ├── identificacion (RUC/CI proveedor)
│   ├── razonSocial
│   ├── fechaEmision
│   ├── tipoComprobante
│   ├── autorizacion
│   ├── baseImponible
│   ├── IVA
│   ├── retencionIR
│   ├── retencionIVA
│   └── formaPago
│
└── ventas[]
    ├── tipoIdentificacion
    ├── identificacion (RUC/CI cliente)
    ├── fechaEmision
    ├── tipoComprobante
    ├── autorizacion
    ├── baseImponible
    └── IVA
```

---

## 10. DIGITAL SIGNATURE

### 10.1 Ley de Firma Electrónica

| Requirement | Implementation |
|:------------|:---------------|
| Certificado digital | BCE, Security Data, etc. |
| Formato XAdES-BES | Para documentos SRI |
| Validez legal | Igual a firma manuscrita |
| Custodia | Almacenar certificado seguro |

### 10.2 Sign Flow

```
FLOW: Firma Digital
┌─────────────────────────────────────────────────────────────┐
│ 1. CERTIFICADO                                              │
│    ├── Obtener de autoridad certificadora                  │
│    ├── Archivo .p12                                         │
│    └── Configurar en Odoo                                  │
│                                                             │
│ 2. FIRMA DOCUMENTO                                          │
│    ├── Generar XML                                          │
│    ├── Calcular hash SHA-256                               │
│    ├── Firmar con clave privada                            │
│    └── Insertar firma XAdES                                │
│                                                             │
│ 3. VALIDACIÓN                                               │
│    ├── Verificar integridad                                │
│    ├── Verificar certificado vigente                       │
│    └── Verificar cadena confianza                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 11. DOCUMENT STATUS

### 11.1 SRS Documents Created

| # | Document | Status |
|:--|:---------|:-------|
| 1 | SRS_L10N_EC_2026.md | ✅ Complete |
| 2 | SRS_WIZARD_COMPANY_EC.md | ✅ Complete |
| 3 | SRS_L10N_EC_DEEP_IMPLEMENTATION.md | ✅ Complete |
| 4 | SRS_L10N_EC_COMPLETE.md | ✅ Complete |
| 5 | SRS_LEGAL_TEST_SCENARIOS.md | ✅ Complete |
| 6 | SRS_PARTNER_TYPES.md | ✅ Complete |
| 7 | SRS_HR_FLOWS.md | ✅ Complete |
| 8 | SRS_INVENTORY_MRP_FLOWS.md | ✅ Complete |
| 9 | SRS_MASTER_MODULES.md | ✅ Complete |

### 11.2 Pending SRS Documents

| # | Document | Module | Priority |
|:--|:---------|:-------|:---------|
| 1 | SRS_EDI_FLOWS.md | l10n_ec_edi | P1 |
| 2 | SRS_WITHHOLDING_FLOWS.md | l10n_ec_withholding | P1 |
| 3 | SRS_REPORTS_ATS.md | l10n_ec_reports | P1 |
| 4 | SRS_POS_FLOWS.md | l10n_ec_pos | P1 |
| 5 | SRS_ASSETS_DEPRECIATION.md | l10n_ec_asset | P2 |

---

**END OF DOCUMENT**
