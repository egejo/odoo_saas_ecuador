# SRS - Legal Test Scenarios
## Ecuador Localization - Based on LORTI, RLOTI, Código Trabajo

**Document ID:** SRS-L10N-EC-SCENARIOS-2026
**Version:** 1.0.0
**Date:** 2026-01-25

---

## 1. SALES SCENARIOS (Invoicing TO Customers)

### 1.1 Customer Types by Law

| Scenario | Demo Partner | RUC Type | Legal Base |
|:---------|:-------------|:---------|:-----------|
| Persona Natural sin RUC | demo_customer_natural | Cédula | LORTI Art. 19 |
| **Tercera Edad (65+)** | demo_customer_tercera_edad | Cédula | LORTI Art. 74 |
| **Persona con Discapacidad** | demo_customer_discapacidad | Cédula | Ley Discap. Art. 78 |
| Persona Natural Obligado | demo_customer_natural_obligado | RUC Natural | LORTI Art. 19, 34 |
| Sociedad Privada | demo_customer_sociedad | RUC 9 | LORTI Art. 98 |
| Contribuyente Especial | demo_customer_especial | RUC + Resolución | NAC-DGERCGC15-00000284 |
| RIMPE Emprendedor | demo_customer_rimpe_e | RUC RIMPE-E | LORTI Art. 97.1-97.7 |
| RIMPE Negocio Popular | demo_customer_rimpe_p | RUC RIMPE-P | LORTI Art. 97.1-97.7 |
| Consumidor Final | demo_customer_final | 9999999999999 | NAC-DGERCGC14-00790 |
| Exportador Habitual | demo_customer_exporter | RUC Exportador | LORTI Art. 55-57 |
| Institución Pública | demo_customer_gobierno | RUC 6 | LORTI Art. 73 |
| Empresa Pública EP | demo_customer_empresa_publica | RUC 6 | LOEP Art. 4 |

### 1.2 Invoice Rules by Customer Type

| Customer Type | IVA | Factura | Retención Recibida |
|:--------------|:----|:--------|:-------------------|
| Consumidor Final ≤$50 | Incluido | Nota de Venta | No |
| Consumidor Final >$50 | 15% | Factura | No |
| Persona Natural | 15% | Factura | Posible |
| Sociedad | 15% | Factura | Sí (si es ART) |
| Contribuyente Especial | 15% | Factura | Sí (obligatoria) |
| Sector Público | 15% | Factura | Sí (100% IR + IVA) |
| Exportación | 0% | Factura Exportación | No |

---

## 2. PURCHASE SCENARIOS (Buying FROM Suppliers)

### 2.1 Retention by Supplier Type

| Scenario | Demo Partner | Code IR | Rate IR | Code IVA | Rate IVA | Legal Base |
|:---------|:-------------|:--------|:--------|:---------|:---------|:-----------|
| Profesional (Honorarios) | demo_supplier_profesional | 303 | 10% | 731 | 100% | LORTI Art. 43 |
| Bienes Muebles | demo_supplier_comercial | 312 | 1% | 721 | 10% | LORTI Art. 45 |
| Contribuyente Especial | demo_supplier_especial | 312 | 1% | 725/727 | 30%/70% | NAC-284 |
| Sin RUC (Liq. Compra) | demo_supplier_informal | 312 | 2% | 729 | 100% | LORTI Art. 36 |
| Arrendamiento Inmueble | demo_supplier_arrendador | 320 | 1.75% | 723 | 20% | LORTI Art. 29 |
| Transporte Privado | demo_supplier_transporte | 310 | 1% | 723 | 20% | LORTI Art. 45 |
| Contratista Estado | demo_supplier_gobierno | Variable | Según tipo | Variable | Según tipo | DE 045-2025 |
| Seguros/Reaseguros | demo_supplier_seguros | 322 | 1% | 723 | 20% | LORTI Art. 45 |
| Rendimiento Financiero | demo_supplier_banco | 323 | 2% | N/A | 0% | LORTI Art. 39 |
| Publicidad | demo_supplier_publicidad | 309 | 1% | 723 | 20% | LORTI Art. 45 |
| Notario/Registrador | demo_supplier_notario | 303 | 10% | 731 | 100% | LORTI Art. 43 |

### 2.2 Retention Matrix

```
            ┌──────────────────────────────────────────────────────────────┐
            │               SUPPLIER (Who you BUY from)                    │
            ├──────────────┬──────────────┬──────────────┬─────────────────┤
BUYER       │ Natural      │ Sociedad     │ Contrib.     │ Sin RUC        │
(You)       │ Profesional  │ General      │ Especial     │ (Liq.Compra)   │
├───────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│Contrib.   │ IR: 10%      │ IR: 1-2%     │ IR: 1-2%     │ IR: 2%         │
│Especial   │ IVA: 100%    │ IVA: 30%/70% │ No IVA       │ IVA: 100%      │
├───────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│Sociedad   │ IR: 10%      │ IR: 1-2%     │ IR: 1-2%     │ IR: 2%         │
│(Art. Ret.)│ IVA: 100%    │ IVA: 10%/20% │ No IVA       │ IVA: 100%      │
├───────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│Sociedad   │ No retiene   │ No retiene   │ No retiene   │ IR: 2%         │
│(No ART)   │              │              │              │ IVA: 100%      │
├───────────┼──────────────┼──────────────┼──────────────┼─────────────────┤
│Sector     │ IR: 10%      │ IR: 1-2%     │ IR: 1-2%     │ IR: 2%         │
│Público    │ IVA: 100%    │ IVA: 100%    │ IVA: 100%    │ IVA: 100%      │
└───────────┴──────────────┴──────────────┴──────────────┴─────────────────┘
```

---

## 3. PAYROLL SCENARIOS (Employees)

### 3.1 Employee Types by Region

| Scenario | Demo Partner | Region | Décimo 4to | Legal Base |
|:---------|:-------------|:-------|:-----------|:-----------|
| Sierra/Oriente | demo_employee_sierra | Sierra | Agosto 15 | CT Art. 113 |
| Costa | demo_employee_costa | Costa | Marzo 15 | CT Art. 113 |
| Galápagos | demo_employee_galapagos | Insular | Marzo 15 | CT Art. 113 |

### 3.2 Payroll Calculations

| Concept | Formula | Demo Value (SBU $482) |
|:--------|:--------|:----------------------|
| IESS Personal | Salario × 9.45% | $45.55 |
| IESS Patronal | Salario × 11.15% | $53.74 |
| SECAP | Salario × 0.50% | $2.41 |
| IECE | Salario × 0.50% | $2.41 |
| Décimo Tercero | Total Ingresos ÷ 12 | Mensualizado |
| Décimo Cuarto | SBU 2026 | $482.00 |
| Fondos Reserva | Salario × 8.33% | $40.15 |
| Vacaciones | Salario ÷ 24 × días | 15 días/año |
| Techo IESS | 25 × SBU | $12,050.00 |

---

## 4. FOREIGN TRANSACTIONS

### 4.1 ISD (Impuesto Salida de Divisas)

| Scenario | Demo Partner | Country | ISD Rate | Legal Base |
|:---------|:-------------|:--------|:---------|:-----------|
| Import from USA | demo_supplier_usa | USA | 5% | LORTI Art. 156 |
| Export to Colombia | demo_customer_colombia | Colombia | 0% | LORTI Art. 159 |

### 4.2 Payments to Foreign

| Payment Type | IR Rate | Legal Base |
|:-------------|:--------|:-----------|
| Services | 25% | LORTI Art. 48 |
| Goods | 0% | N/A |
| Royalties | 25% | LORTI Art. 48 |
| Interest | 25% | LORTI Art. 48 |
| Tax Haven | 25% + 10% | LORTI Art. 13 |

---

## 5. SPECIAL SCENARIOS

### 5.1 Government Contracts (DE 045-2025)

| Scenario | Demo Partner | Requirement | Penalty |
|:---------|:-------------|:------------|:--------|
| Contractor sells TO Gov | demo_customer_gobierno | Standard invoice | N/A |
| Contractor buys FOR Gov | demo_supplier_gobierno | UAF Certificate | Up to 5% daily |

### 5.2 IVA Refund Benefits (LORTI Art. 74, Ley Discapacidades Art. 78)

| Beneficiary | Demo Partner | Monthly Limit | Condition | Legal Base |
|:------------|:-------------|:--------------|:----------|:-----------|
| Tercera Edad (65+) | demo_customer_tercera_edad | 5 canastas básicas ($4,044.75) | Edad ≥ 65 años | LORTI Art. 74 |
| Discapacidad | demo_customer_discapacidad | 3 SBU ($1,446) | Carnet CONADIS ≥30% | Ley Discap. Art. 78 |

**IVA Refund Process:**
1. Customer purchases goods/services with IVA
2. Customer requests refund to SRI (online or presencial)
3. SRI verifies eligibility (age/disability)
4. Refund deposited to bank account

**Fields Required in res.partner:**
- `l10n_ec_tercera_edad`: Boolean
- `l10n_ec_discapacidad`: Boolean
- `l10n_ec_discapacidad_porcentaje`: Integer (30-100%)
- `l10n_ec_discapacidad_carnet`: Char (CONADIS number)

### 5.3 Electronic Documents

| Document Type | Code | Legal Base |
|:--------------|:-----|:-----------|
| Factura | 01 | NAC-DGERCGC25-17 |
| Liquidación Compra | 03 | NAC-DGERCGC25-17 |
| Nota Crédito | 04 | NAC-DGERCGC25-17 |
| Nota Débito | 05 | NAC-DGERCGC25-17 |
| Guía Remisión | 06 | NAC-DGERCGC25-17 |
| Comprobante Retención | 07 | NAC-DGERCGC25-17 |

---

## 6. DEMO PARTNERS SUMMARY

### 6.1 Total Count

| Category | Count |
|:---------|:------|
| Customers | 12 |
| Suppliers | 11 |
| Employees | 3 |
| Foreign | 2 |
| **TOTAL** | **28** |

### 6.2 Complete List

**CUSTOMERS (10):**
1. demo_customer_natural - Persona Natural (Cédula)
2. demo_customer_natural_obligado - Natural con RUC
3. demo_customer_sociedad - Sociedad Privada
4. demo_customer_especial - Contribuyente Especial
5. demo_customer_rimpe_e - RIMPE Emprendedor
6. demo_customer_rimpe_p - RIMPE Negocio Popular
7. demo_customer_final - Consumidor Final
8. demo_customer_exporter - Exportador Habitual
9. demo_customer_gobierno - Municipio (Sector Público)
10. demo_customer_empresa_publica - Empresa Pública EP

**SUPPLIERS (11):**
1. demo_supplier_profesional - Honorarios 303 (10%)
2. demo_supplier_comercial - Bienes 312 (1%)
3. demo_supplier_especial - Contrib. Especial
4. demo_supplier_informal - Liq. Compra 729 (100%)
5. demo_supplier_arrendador - Inmuebles 320 (1.75%)
6. demo_supplier_transporte - Transporte 310 (1%)
7. demo_supplier_gobierno - Contratista Estado (UAF)
8. demo_supplier_seguros - Seguros 322 (1%)
9. demo_supplier_banco - Banco 323 (2%)
10. demo_supplier_publicidad - Publicidad 309 (1%)
11. demo_supplier_notario - Notario 303 (10%)

**EMPLOYEES (3):**
1. demo_employee_sierra - Quito (Agosto)
2. demo_employee_costa - Guayaquil (Marzo)
3. demo_employee_galapagos - Santa Cruz (Marzo)

**FOREIGN (2):**
1. demo_supplier_usa - ISD 5%
2. demo_customer_colombia - Exportación

---

## 7. LEGAL REFERENCES

| Code | Law | Description |
|:-----|:----|:------------|
| LORTI | Ley Orgánica de Régimen Tributario Interno | Tax law |
| RLORTI | Reglamento LORTI | Tax regulations |
| CT | Código del Trabajo | Labor law |
| LOEP | Ley Orgánica de Empresas Públicas | Public companies |
| NAC-DGERCGC25-17 | Resolución SRI 2025 | E-invoicing |
| DE 045-2025 | Decreto Ejecutivo | Gov contracts |
| NAC-284 | Resolución Contrib. Especial | Special taxpayer |

---

**END OF DOCUMENT**
