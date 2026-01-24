# Manual de Usuario - Localización Ecuador

## 🇪🇨 Odoo Ecuador (SRI 2026)

**Por [Somatech.dev](https://somatech.dev)**

---

## 1. Introducción

Esta guía explica cómo usar los módulos de localización ecuatoriana para Odoo 18, cumpliendo con todas las regulaciones del SRI 2026.

---

## 2. Configuración Inicial

### 2.1 Datos de la Empresa

**Configuración > Empresas > Su Empresa**

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| RUC | 13 dígitos | 1791234567001 |
| Razón Social | Nombre legal | Mi Empresa S.A. |
| Dirección | Dirección fiscal | Quito, Ecuador |

### 2.2 Certificado Digital SRI

**Contabilidad > Configuración > Ecuador SRI > Certificados**

1. Haga clic en **Crear**
2. Suba su archivo `.p12`
3. Ingrese la contraseña del certificado
4. Configure la fecha de vencimiento
5. Haga clic en **Activar**

> ⚠️ **Importante**: El certificado debe ser de un proveedor autorizado (Security Data, ANF AC, BCE)

### 2.3 Ambiente SRI

**Configuración > Empresas > Ecuador SRI**

- **Pruebas**: Para desarrollo y pruebas
- **Producción**: Para facturas reales al SRI

---

## 3. Facturación Electrónica

### 3.1 Crear Factura

1. Vaya a **Contabilidad > Clientes > Facturas**
2. Haga clic en **Crear**
3. Seleccione el cliente
4. Agregue líneas de productos
5. **Confirmar** la factura

### 3.2 Enviar al SRI

1. Haga clic en el botón **Enviar a SRI**
2. Espere la respuesta:
   - ✅ **AUTORIZADO**: Factura válida
   - ❌ **RECHAZADO**: Revisar errores

### 3.3 Reimprimir RIDE

1. Abra la factura autorizada
2. Haga clic en **Imprimir > RIDE**
3. Se genera el PDF con código de barras

### 3.4 Consumidor Final

- Límite máximo: **$50.00 USD**
- RUC automático: 9999999999999
- ⚠️ **No se puede anular** (regla SRI 2026)

---

## 4. Retenciones

### 4.1 Crear Retención

1. Vaya a **Contabilidad > Proveedores > Retenciones**
2. Haga clic en **Crear**
3. Seleccione la factura del proveedor
4. Agregue líneas de retención:
   - Retención IR (ej: 303 = 10%)
   - Retención IVA (ej: 721 = 10%)
5. **Validar** la retención

### 4.2 Regla 5 Días

> ⚠️ La retención debe emitirse dentro de **5 días hábiles** desde la fecha de la factura

El sistema bloqueará retenciones fuera de plazo.

### 4.3 Códigos Comunes

**Retención IR:**
| Código | % | Concepto |
|--------|---|----------|
| 303 | 10% | Honorarios Profesionales |
| 304 | 8% | Servicios Predomina Intelecto |
| 312 | 1% | Bienes Muebles |

**Retención IVA:**
| Código | % | Aplicación |
|--------|---|------------|
| 721 | 10% | Bienes |
| 723 | 20% | Servicios |
| 729 | 100% | Liquidación de Compra |

---

## 5. Guía de Remisión

### 5.1 Crear Guía

1. Vaya a **Inventario > Entregas**
2. Abra una entrega confirmada
3. Haga clic en **Generar Guía de Remisión**
4. Complete datos del transportista
5. **Enviar a SRI**

### 5.2 Datos Requeridos

- Placa del vehículo
- RUC/Cédula del transportista
- Motivo de traslado

---

## 6. Nómina

### 6.1 Rol de Pagos

**Recursos Humanos > Nómina > Roles**

El sistema calcula automáticamente:
- Sueldo base
- IESS Personal (9.45%)
- IESS Patronal (12.15%)
- Horas extras

### 6.2 Décimo Tercero

- **Cálculo**: Ingresos totales ÷ 12
- **Período**: 1 Dic - 30 Nov
- **Pago**: Antes del **24 de diciembre**

### 6.3 Décimo Cuarto

- **Monto**: 1 SBU = **$482** (2026)
- **Costa/Galápagos**: Antes del **15 de marzo**
- **Sierra/Amazonía**: Antes del **15 de agosto**

### 6.4 Utilidades

- **Porcentaje**: 15% de utilidad neta
- **Individual**: 10% (por días trabajados)
- **Familiar**: 5% (por cargas familiares)
- **Pago**: Antes del **15 de abril**

---

## 7. Reportes

### 7.1 ATS (Anexo Transaccional Simplificado)

**Contabilidad > Reportes > Ecuador > ATS**

1. Seleccione el mes
2. Haga clic en **Generar ATS**
3. Descargue el archivo XML
4. Suba a portal SRI

### 7.2 Contenido del ATS

- Ventas del período
- Compras del período
- Retenciones emitidas
- Documentos anulados

---

## 8. Preguntas Frecuentes

### ¿Qué hago si el SRI rechaza mi factura?

1. Revise el mensaje de error
2. Corrija el problema
3. Intente nuevamente

### ¿Puedo anular una factura autorizada?

- ✅ Facturas normales: Sí, dentro de **7 días**
- ❌ Consumidor Final: **No permitido**

### ¿Cómo renuevo mi certificado?

1. Obtenga nuevo certificado del proveedor
2. Suba el nuevo .p12 en Odoo
3. Active el nuevo certificado
4. Desactive el anterior

---

## 9. Soporte

**Email**: soporte@somatech.dev
**Web**: [somatech.dev](https://somatech.dev)
**GitHub**: [github.com/somatechlat/odoo_saas_ecuador](https://github.com/somatechlat/odoo_saas_ecuador)

---

**Licencia**: LGPL-3.0
