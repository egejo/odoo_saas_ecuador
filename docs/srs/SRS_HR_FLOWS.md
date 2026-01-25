# SRS - HR Flows Ecuador
## Complete Human Resources Processes - Código del Trabajo

**Document ID:** SRS-L10N-EC-HR-FLOWS
**Version:** 1.0.0
**Date:** 2026-01-25
**Status:** PLANNING

---

## 1. HIRING PROCESS FLOW

### 1.1 Pre-Hiring Phase

```
FLOW: Pre-Contratación
┌─────────────────────────────────────────────────────────────┐
│ 1. REQUISICIÓN                                              │
│    ├── Solicitud de personal                                │
│    ├── Aprobación presupuestaria                           │
│    └── Definición del perfil                               │
│                                                             │
│ 2. SELECCIÓN                                                │
│    ├── Publicación vacante                                  │
│    ├── Recepción hojas de vida                             │
│    ├── Entrevistas                                          │
│    └── Selección candidato                                 │
│                                                             │
│ 3. VERIFICACIÓN                                             │
│    ├── Validar cédula (Registro Civil API)                 │
│    ├── Verificar afiliación IESS                           │
│    ├── Antecedentes (si aplica)                            │
│    └── Referencias laborales                               │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Contract Creation Phase

```
FLOW: Creación de Contrato
┌─────────────────────────────────────────────────────────────┐
│ 1. DATOS EMPLEADO                                           │
│    ├── Cédula → Validar Módulo 10                          │
│    ├── Fecha nacimiento → Calcular edad                    │
│    ├── Dirección → Provincia (Sierra/Costa/Oriente)        │
│    └── Cuenta bancaria                                      │
│                                                             │
│ 2. TIPO DE CONTRATO (CT Art. 12-17)                        │
│    ├── Indefinido (default después de 90 días)             │
│    ├── A plazo fijo (máx 2 años)                           │
│    ├── Eventual (máx 180 días)                             │
│    ├── Ocasional (máx 30 días)                             │
│    ├── Por obra cierta                                      │
│    ├── Por tarea                                            │
│    ├── A destajo                                            │
│    └── Aprendizaje                                          │
│                                                             │
│ 3. JORNADA DE TRABAJO (CT Art. 47-55)                      │
│    ├── Completa: 8h/día, 40h/semana                        │
│    ├── Parcial: < 40h/semana                               │
│    ├── Nocturna: 19:00-06:00 (+25%)                        │
│    └── Mixta                                                │
│                                                             │
│ 4. REMUNERACIÓN                                             │
│    ├── Salario >= SBU ($482 en 2026)                       │
│    ├── Componentes salariales                              │
│    └── Beneficios adicionales                              │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 MDT Registration (Sistema SUT)

```
FLOW: Registro Contrato en Ministerio del Trabajo
┌─────────────────────────────────────────────────────────────┐
│ 1. GENERAR CONTRATO PDF                                     │
│    ├── Datos empleador (RUC, razón social)                 │
│    ├── Datos trabajador (cédula, nombres)                  │
│    ├── Tipo contrato, jornada, salario                     │
│    └── Firmas digitales                                     │
│                                                             │
│ 2. SUBIR A SUT (Sistema Único de Trabajo)                  │
│    ├── Endpoint: sut.trabajo.gob.ec                        │
│    ├── Autenticación con certificado                       │
│    ├── Upload XML/PDF                                       │
│    └── Obtener número de registro                          │
│                                                             │
│ 3. PLAZO                                                    │
│    └── 15 días desde inicio de labores (CT Art. 20)        │
│                                                             │
│ 4. MULTA POR INCUMPLIMIENTO                                │
│    └── 3-20 SBU por contrato no registrado                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. LEAVE OF ABSENCE TYPES

### 2.1 Paid Leaves (Permisos Remunerados)

| Leave Type | Duration | Legal Base | Required Docs |
|:-----------|:---------|:-----------|:--------------|
| **Vacaciones** | 15 días/año | CT Art. 69-78 | Solicitud |
| **Enfermedad (3 días)** | Hasta 3 días | CT Art. 42 num. 19 | Certificado médico |
| **Enfermedad (IESS)** | Desde día 4 | IESS | Certificado IESS |
| **Maternidad** | 12 semanas | CT Art. 152 | Certificado prenatal |
| **Paternidad** | 10 días | CT Art. 152 | Partida nacimiento |
| **Lactancia** | 2h/día × 12 meses | CT Art. 155 | Partida nacimiento |
| **Calamidad Doméstica** | Hasta 3 días | CT Art. 42 num. 30 | Justificación |
| **Matrimonio** | 3 días | CT Art. 42 num. 31 | Acta matrimonio |
| **Fallecimiento Familiar** | 3 días | CT Art. 42 num. 30 | Acta defunción |
| **Estudios** | Según convenio | CT Art. 42 num. 27 | Matrícula |

### 2.2 Unpaid Leaves (Permisos No Remunerados)

| Leave Type | Duration | Legal Base | Conditions |
|:-----------|:---------|:-----------|:-----------|
| **Licencia sin sueldo** | Acordado | CT Art. 173 | Mutuo acuerdo |
| **Dirigencia sindical** | Según estatuto | CT Art. 451 | Trabajador sindicalizado |

### 2.3 Leave Flow

```
FLOW: Solicitud de Permiso
┌─────────────────────────────────────────────────────────────┐
│ 1. SOLICITUD                                                │
│    ├── Empleado crea solicitud                             │
│    ├── Tipo de permiso                                      │
│    ├── Fechas (desde - hasta)                              │
│    └── Documentos adjuntos                                  │
│                                                             │
│ 2. APROBACIÓN                                               │
│    ├── Supervisor revisa                                    │
│    ├── RRHH valida                                          │
│    └── Aprobación/Rechazo                                  │
│                                                             │
│ 3. REGISTRO                                                 │
│    ├── Actualizar calendario                               │
│    ├── Afectar nómina (si aplica)                         │
│    └── Reportar IESS (enfermedad >3 días)                  │
│                                                             │
│ 4. RETORNO                                                  │
│    ├── Validar reincorporación                             │
│    └── Actualizar estado                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. PAYROLL PERIODS

### 3.1 Payment Frequency

| Frequency | Legal Base | Notes |
|:----------|:-----------|:------|
| Mensual | CT Art. 82 | Default |
| Quincenal | CT Art. 82 | Si se pacta |
| Semanal | CT Art. 82 | Si se pacta |

### 3.2 Mandatory Payments

| Payment | When | Amount | Legal Base |
|:--------|:-----|:-------|:-----------|
| **Décimo Tercero** | Hasta Dic 24 | Total ingresos ÷ 12 | CT Art. 111 |
| **Décimo Cuarto** | Sierra: Ago 15, Costa: Mar 15 | 1 SBU | CT Art. 113 |
| **Fondos de Reserva** | Mensual (después año 1) | 8.33% salario | CT Art. 196 |
| **Utilidades** | Hasta Abr 15 | 15% utilidades | CT Art. 97 |

---

## 4. TERMINATION FLOWS

### 4.1 Termination Types

| Type | Initiative | Liquidation | Legal Base |
|:-----|:-----------|:------------|:-----------|
| **Renuncia voluntaria** | Trabajador | Proporcional | CT Art. 184 |
| **Desahucio** | Cualquiera | 25% por año | CT Art. 184-185 |
| **Visto Bueno Empleador** | Empleador | Solo proporcional | CT Art. 172 |
| **Visto Bueno Trabajador** | Trabajador | Indemnización | CT Art. 173 |
| **Despido Intempestivo** | Empleador | 3m + 1m/año | CT Art. 188 |
| **Fin de Contrato** | Automático | Según tipo | CT Art. 169 |

### 4.2 Liquidation Calculation

```
LIQUIDATION = {
    # SIEMPRE:
    + Salario proporcional (días trabajados mes actual)
    + Vacaciones no gozadas
    + Décimo Tercero proporcional
    + Décimo Cuarto proporcional
    + Horas extras pendientes

    # SI APLICA:
    + Bonificación desahucio (25% × años)        # Si desahucio
    + Indemnización despido (3m + 1m × años)     # Si despido intempestivo
    + Jubilación patronal                        # Si > 25 años

    # DESCUENTOS:
    - Préstamos pendientes
    - Anticipos
    - Multas (si aplica)
}
```

### 4.3 Termination Flow

```
FLOW: Terminación Laboral
┌─────────────────────────────────────────────────────────────┐
│ 1. CAUSA DE TERMINACIÓN                                     │
│    ├── Seleccionar tipo                                     │
│    ├── Documentar causa                                     │
│    └── Fecha efectiva                                       │
│                                                             │
│ 2. CÁLCULO LIQUIDACIÓN                                      │
│    ├── Ejecutar cálculo automático                         │
│    ├── Revisar componentes                                  │
│    └── Aprobar liquidación                                 │
│                                                             │
│ 3. REGISTRO MDT/IESS                                        │
│    ├── Aviso de salida IESS (dentro de 3 días)             │
│    ├── Acta de finiquito MDT                               │
│    └── Obtener acuse de recibo                             │
│                                                             │
│ 4. PAGO                                                     │
│    ├── Generar cheque/transferencia                        │
│    ├── Firma de finiquito                                  │
│    └── Archivo expediente                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. IESS INTEGRATION

### 5.1 IESS Processes

| Process | When | System | Deadline |
|:--------|:-----|:-------|:---------|
| **Aviso de Entrada** | Nueva contratación | IESS Online | 15 días |
| **Aviso de Salida** | Terminación | IESS Online | 3 días |
| **Planilla Mensual** | Cada mes | IESS Online | Día 15 mes siguiente |
| **Fondos de Reserva** | Mensual | IESS Online | Con planilla |
| **Préstamos Quirografarios** | Cuando aplique | IESS Online | Descuento nómina |
| **Préstamos Hipotecarios** | Cuando aplique | IESS Online | Descuento nómina |

### 5.2 IESS API Integration

```
ENDPOINTS IESS:
- Consulta afiliación: verificar_afiliado(cedula)
- Aviso entrada: registrar_entrada(empleado_data)
- Aviso salida: registrar_salida(empleado_data, fecha)
- Planilla: enviar_planilla(periodo, empleados)
- Certificado aportes: obtener_certificado(cedula)
```

---

## 6. SAFETY AND HEALTH (SST)

### 6.1 Requirements (DE 2393)

| Requirement | Threshold | Legal Base |
|:------------|:----------|:-----------|
| Reglamento Interno SST | > 10 empleados | DE 2393 Art. 11 |
| Comité SST | > 15 empleados | DE 2393 Art. 13 |
| Unidad de SST | > 100 empleados | DE 2393 Art. 15 |
| Médico Ocupacional | > 100 empleados | DE 2393 Art. 16 |
| Programa de SST | Todos | MDT-2024-196 |

### 6.2 Accident Flow

```
FLOW: Accidente de Trabajo
┌─────────────────────────────────────────────────────────────┐
│ 1. OCURRENCIA                                               │
│    ├── Atención médica inmediata                           │
│    ├── Notificar supervisor                                 │
│    └── Documentar incidente                                │
│                                                             │
│ 2. REPORTE (48 horas)                                       │
│    ├── Formulario aviso accidente                          │
│    ├── Enviar a IESS (Riesgos del Trabajo)                │
│    └── Enviar a MDT (SUT)                                  │
│                                                             │
│ 3. INVESTIGACIÓN                                            │
│    ├── Análisis de causas                                  │
│    ├── Medidas correctivas                                 │
│    └── Informe final                                       │
│                                                             │
│ 4. SEGUIMIENTO                                              │
│    ├── Subsidio IESS durante incapacidad                   │
│    ├── Rehabilitación                                       │
│    └── Reintegro laboral                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. DEMO EMPLOYEES

### 7.1 Current Demo Employees

| Partner | Region | Purpose |
|:--------|:-------|:--------|
| demo_employee_sierra | Quito (Sierra) | Décimo Cuarto Agosto |
| demo_employee_costa | Guayaquil (Costa) | Décimo Cuarto Marzo |
| demo_employee_galapagos | Santa Cruz (Insular) | Beneficios especiales |

### 7.2 Proposed Additional Employees

| Partner | Contract Type | Purpose |
|:--------|:--------------|:--------|
| demo_employee_plazo_fijo | A plazo fijo | Test terminación |
| demo_employee_eventual | Eventual | Test 180 días máx |
| demo_employee_medio_tiempo | Parcial | Test jornada parcial |
| demo_employee_discapacidad | Indefinido | Beneficios discapacidad |
| demo_employee_tercera_edad | Indefinido | Trabajador > 65 años |
| demo_employee_maternidad | Indefinido | Test licencia maternidad |

---

## 8. ODOO MODULE MAPPING

### 8.1 Required Odoo Modules

| Module | Purpose | Customization |
|:-------|:--------|:--------------|
| hr | Empleados base | Campos Ecuador |
| hr_contract | Contratos | Tipos CT |
| hr_holidays | Permisos/Vacaciones | Tipos Ecuador |
| hr_attendance | Control asistencia | DE 255 |
| hr_payroll | Nómina | Cálculos Ecuador |
| hr_expense | Gastos | LORTI deducibles |

### 8.2 New Models Required

| Model | Purpose |
|:------|:--------|
| l10n_ec.hr.contract.type | Tipos contrato CT |
| l10n_ec.hr.leave.type | Tipos permiso Ecuador |
| l10n_ec.hr.termination | Liquidaciones |
| l10n_ec.hr.mdt.registration | Registro MDT |
| l10n_ec.hr.iess.planilla | Planillas IESS |

---

**END OF DOCUMENT**
