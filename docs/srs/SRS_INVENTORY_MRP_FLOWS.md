# SRS - Inventory & Logistics Flows Ecuador
## Stock, Shipping, Guía de Remisión - COPCI, LOTTTSV

**Document ID:** SRS-L10N-EC-INVENTORY-FLOWS
**Version:** 1.0.0
**Date:** 2026-01-25
**Status:** PLANNING

---

## 1. GUÍA DE REMISIÓN (Waybill)

### 1.1 Legal Requirement

| Regulation | Requirement |
|:-----------|:------------|
| COPCI Art. 142 | Mercadería en tránsito debe tener guía |
| NAC-DGERCGC25-17 | Guía de remisión electrónica obligatoria |
| LOTTTSV Art. 45 | Documento requerido para transporte |

### 1.2 When Required

| Scenario | Guía Required | Notes |
|:---------|:--------------|:------|
| Venta con entrega propia | ✅ Sí | Emisor = vendedor |
| Venta con transporte tercero | ✅ Sí | Emisor = transportista |
| Traslado entre bodegas | ✅ Sí | Mismo RUC |
| Devolución de mercadería | ✅ Sí | Con referencia a factura |
| Mercadería en consignación | ✅ Sí | Sin transferencia propiedad |
| Compras ≤ $300 | ❌ No | Factura basta |

### 1.3 Guía de Remisión Flow

```
FLOW: Emisión Guía de Remisión
┌─────────────────────────────────────────────────────────────┐
│ 1. ORIGEN                                                   │
│    ├── Orden de venta confirmada                           │
│    ├── O: Transferencia interna                            │
│    └── Fecha/hora de inicio traslado                       │
│                                                             │
│ 2. DATOS OBLIGATORIOS                                       │
│    ├── Remitente (RUC, razón social, dirección)            │
│    ├── Destinatario (RUC/CI, nombre, dirección)            │
│    ├── Transportista (RUC, nombre, placa vehículo)         │
│    ├── Punto partida (dirección, establecimiento)          │
│    ├── Punto llegada (dirección)                           │
│    ├── Motivo traslado                                      │
│    └── Detalle mercadería (código, descripción, cantidad)  │
│                                                             │
│ 3. GENERACIÓN XML                                           │
│    ├── Estructura según XSD SRI                            │
│    ├── Clave de acceso 49 dígitos                          │
│    ├── Firma XAdES-BES                                      │
│    └── Envío a SRI                                         │
│                                                             │
│ 4. AUTORIZACIÓN                                             │
│    ├── Recibir respuesta SRI                               │
│    ├── Guardar número autorización                         │
│    └── Generar RIDE (PDF)                                  │
│                                                             │
│ 5. TRANSPORTE                                               │
│    ├── Conductor porta RIDE impreso                        │
│    ├── Vigencia: 24h dentro ciudad, 72h interprovincial    │
│    └── Mercadería debe coincidir con guía                  │
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Motivos de Traslado

| Code | Description | Use Case |
|:-----|:------------|:---------|
| 01 | Venta | Entrega por venta |
| 02 | Compra | Recepción por compra |
| 03 | Consignación | Sin transferencia |
| 04 | Devolución | Mercadería devuelta |
| 05 | Traslado entre establecimientos | Mismo RUC |
| 06 | Exportación | A puerto/aeropuerto |
| 07 | Importación | Desde aduana |
| 21 | Otros | Especificar |

---

## 2. INVENTORY MANAGEMENT

### 2.1 Warehouse Structure

```
STRUCTURE: Bodegas Ecuador
┌─────────────────────────────────────────────────────────────┐
│ EMPRESA (res.company)                                       │
│ └── RUC, Razón Social                                       │
│                                                             │
│ ESTABLECIMIENTO (l10n_ec.establishment)                     │
│ ├── Código (3 dígitos)                                      │
│ ├── Dirección                                               │
│ └── SRI: Punto de emisión                                  │
│                                                             │
│ BODEGA (stock.warehouse)                                    │
│ ├── Linked to establishment                                 │
│ ├── Ubicaciones (stock.location)                           │
│ └── Rutas                                                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Stock Moves with Guía

| Move Type | Guía Required | Document |
|:----------|:--------------|:---------|
| Delivery (sale) | ✅ Yes | Guía saliente |
| Receipt (purchase) | ❌ No | Proveedor emite |
| Internal transfer | ✅ Yes | Guía interna |
| Manufacturing | ❌ No | Interno |
| Scrap | ❌ No | Acta de baja |

---

## 3. LOT & SERIAL TRACKING

### 3.1 Traceability Requirements

| Industry | Requirement | Legal Base |
|:---------|:------------|:-----------|
| Alimentos | Lote + Fecha vencimiento | ARCSA-DE-067 |
| Medicamentos | Lote + Serial + Registro | ARCSA |
| Electrónicos | Serial único | ARCOTEL |
| Vehículos | VIN + Placa | ANT |

### 3.2 Lot Fields

```python
class StockLot(models.Model):
    # Standard
    name = Char  # Lot number
    product_id = Many2one

    # Ecuador extensions
    l10n_ec_registro_sanitario = Char  # ARCSA registration
    l10n_ec_fecha_elaboracion = Date   # Manufacturing date
    l10n_ec_fecha_vencimiento = Date   # Expiry date
    l10n_ec_pais_origen = Many2one     # Country of origin
    l10n_ec_notificacion_sanitaria = Char  # Health notification
```

---

## 4. VALUATION & COSTING

### 4.1 Costing Methods (NIIF)

| Method | NIIF | Use Case |
|:-------|:-----|:---------|
| **FIFO** | NIC 2 | Perecederos, default |
| **Average** | NIC 2 | Commodities |
| **Standard** | NIC 2 | Manufactura |
| **LIFO** | ❌ No permitido | - |

### 4.2 Cost Components (COPCI Art. 108)

```
IMPORTED GOODS COST:
┌─────────────────────────────────────────────────────────────┐
│ FOB (Free on Board)                                         │
│ + Flete internacional                                       │
│ + Seguro internacional                                      │
│ = CIF (Cost, Insurance, Freight)                           │
│                                                             │
│ + AD-VALOREM (arancel)                                      │
│ + FODINFA (0.5%)                                            │
│ + IVA importación (15%)                                     │
│ + Salvaguardia (si aplica)                                 │
│ + Agente aduanas                                            │
│ + Almacenaje                                                │
│ + Transporte interno                                        │
│ = COSTO TOTAL                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. MRP (Manufacturing)

### 5.1 INEN Compliance

| Standard | Applies To | Requirement |
|:---------|:-----------|:------------|
| RTE INEN 142 | Alimentos | Etiquetado nutricional |
| RTE INEN 004 | Textiles | Composición fibras |
| RTE INEN 022 | Electrónicos | Seguridad eléctrica |
| RTE INEN 034 | Juguetes | Seguridad |

### 5.2 Production Flow

```
FLOW: Producción con Normativa Ecuador
┌─────────────────────────────────────────────────────────────┐
│ 1. ORDEN DE PRODUCCIÓN                                      │
│    ├── BOM (Lista de materiales)                           │
│    ├── Routing (Operaciones)                               │
│    └── Cantidad a producir                                 │
│                                                             │
│ 2. CONSUMO MATERIALES                                       │
│    ├── Reservar stock                                       │
│    ├── Registrar lotes consumidos                          │
│    └── Trazabilidad completa                               │
│                                                             │
│ 3. CONTROL CALIDAD                                          │
│    ├── Puntos de control INEN                              │
│    ├── Registrar mediciones                                │
│    └── Aprobar/Rechazar                                    │
│                                                             │
│ 4. PRODUCTO TERMINADO                                       │
│    ├── Asignar lote                                         │
│    ├── Fecha elaboración = hoy                             │
│    ├── Fecha vencimiento = elaboración + vida útil         │
│    ├── Registro sanitario (si aplica)                      │
│    └── Etiquetado INEN                                     │
│                                                             │
│ 5. ALMACENAMIENTO                                           │
│    ├── Ubicación según tipo producto                       │
│    └── FEFO para perecederos                               │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 BOM Extensions

```python
class MrpBom(models.Model):
    # Ecuador extensions
    l10n_ec_registro_sanitario = Char      # ARCSA for this product
    l10n_ec_norma_inen = Char              # INEN standard
    l10n_ec_vida_util_dias = Integer       # Shelf life in days
    l10n_ec_condiciones_almacenamiento = Text  # Storage conditions
```

---

## 6. QUALITY CONTROL (ARCSA)

### 6.1 ARCSA Requirements

| Product Type | Requirement | Document |
|:-------------|:------------|:---------|
| Alimentos procesados | Registro Sanitario | ARCSA-DE-067 |
| Cosméticos | Notificación Sanitaria | ARCSA-DE-042 |
| Medicamentos | Registro Sanitario | ARCSA |
| Dispositivos médicos | Registro Sanitario | ARCSA |

### 6.2 Quality Checks

```
FLOW: Control Calidad ARCSA
┌─────────────────────────────────────────────────────────────┐
│ 1. RECEPCIÓN MATERIA PRIMA                                  │
│    ├── Verificar certificado análisis                      │
│    ├── Verificar fecha vencimiento                         │
│    ├── Inspección visual                                    │
│    └── Muestreo si aplica                                  │
│                                                             │
│ 2. EN PROCESO                                               │
│    ├── Puntos críticos de control (HACCP)                  │
│    ├── Registrar temperatura, pH, etc.                     │
│    └── Verificar parámetros INEN                           │
│                                                             │
│ 3. PRODUCTO TERMINADO                                       │
│    ├── Análisis laboratorio                                │
│    ├── Verificar especificaciones                          │
│    ├── Aprobar liberación                                  │
│    └── Certificado de calidad                              │
│                                                             │
│ 4. TRAZABILIDAD                                             │
│    ├── Lote → Materias primas usadas                       │
│    ├── Lote → Análisis realizados                          │
│    └── Lote → Clientes vendidos                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. CUSTOMS (SENAE)

### 7.1 Import Flow

```
FLOW: Importación (COPCI Art. 108-216)
┌─────────────────────────────────────────────────────────────┐
│ 1. DOCUMENTOS PREVIOS                                       │
│    ├── Factura comercial                                    │
│    ├── Packing list                                         │
│    ├── Conocimiento de embarque (B/L o AWB)                │
│    ├── Certificado origen (si aplica)                      │
│    └── Permisos previos (INEN, ARCSA, MAG)                 │
│                                                             │
│ 2. DAU (Declaración Aduanera Única)                        │
│    ├── Sistema ECUAPASS                                     │
│    ├── Clasificación arancelaria                           │
│    ├── Valor aduanero (CIF)                                │
│    └── Cálculo tributos                                    │
│                                                             │
│ 3. TRIBUTOS                                                 │
│    ├── AD-VALOREM: % según partida                         │
│    ├── FODINFA: 0.5% CIF                                   │
│    ├── IVA: 15% (CIF + ADV + FODINFA)                      │
│    ├── ICE: si aplica                                       │
│    └── Salvaguardia: si aplica                             │
│                                                             │
│ 4. AFORO                                                    │
│    ├── Automático (verde)                                  │
│    ├── Documental (amarillo)                               │
│    └── Físico (rojo)                                       │
│                                                             │
│ 5. LEVANTE                                                  │
│    ├── Pago tributos                                        │
│    ├── Autorización retiro                                 │
│    └── Guía de remisión desde puerto/aeropuerto            │
└─────────────────────────────────────────────────────────────┘
```

### 7.2 Export Flow

```
FLOW: Exportación
┌─────────────────────────────────────────────────────────────┐
│ 1. DOCUMENTOS                                               │
│    ├── Factura exportación (IVA 0%)                        │
│    ├── DAE (Declaración Aduanera Exportación)              │
│    ├── Certificado origen                                   │
│    └── Permisos (MAG para agrícolas)                       │
│                                                             │
│ 2. SISTEMA ECUAPASS                                         │
│    ├── Registro exportador                                  │
│    ├── Transmisión DAE                                      │
│    └── Orden de embarque                                   │
│                                                             │
│ 3. EMBARQUE                                                 │
│    ├── Guía remisión a puerto/aeropuerto                   │
│    ├── Verificación SENAE                                   │
│    └── Pase de salida                                      │
│                                                             │
│ 4. BENEFICIOS FISCALES                                      │
│    ├── IVA 0%                                               │
│    ├── Devolución IVA compras (drawback)                   │
│    └── Exención ISD pagos recibidos                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. FLEET (Transport)

### 8.1 LOTTTSV Requirements

| Requirement | Legal Base | Odoo Module |
|:------------|:-----------|:------------|
| Registro vehículo | LOTTTSV Art. 45 | fleet.vehicle |
| Licencia conductor | LOTTTSV Art. 89 | fleet.vehicle.driver |
| Revisión técnica | LOTTTSV Art. 88 | fleet.vehicle.log |
| SOAT | Ley SOAT | fleet.vehicle.insurance |
| Matrícula | ANT | fleet.vehicle |

### 8.2 Vehicle for Guía

```python
class FleetVehicle(models.Model):
    # Ecuador extensions for Guía de Remisión
    l10n_ec_placa = Char  # Required for guía
    l10n_ec_tipo_vehiculo = Selection([
        ('liviano', 'Liviano'),
        ('pesado', 'Pesado'),
        ('especial', 'Especial'),
    ])
    l10n_ec_capacidad_carga = Float  # Tons
```

---

## 9. DEMO DATA

### 9.1 Products

| Product | Type | Lot Required | INEN |
|:--------|:-----|:-------------|:-----|
| demo_product_alimento | Consumible | ✅ Yes | RTE 142 |
| demo_product_electronico | Stockable | ✅ Serial | RTE 022 |
| demo_product_servicio | Servicio | ❌ No | - |
| demo_product_importado | Stockable | ✅ Yes | - |

### 9.2 Warehouses

| Warehouse | Establishment | Purpose |
|:----------|:--------------|:--------|
| Bodega Principal UIO | 001 | Matriz |
| Bodega Guayaquil | 002 | Sucursal |
| Bodega ZEDE | 003 | Zona especial |

---

## 10. ODOO MODULE MAPPING

### 10.1 Required Modules

| Module | Purpose | Customization |
|:-------|:--------|:--------------|
| stock | Inventario | Guía remisión |
| stock_landed_costs | Costos importación | Tributos SENAE |
| mrp | Manufactura | Lotes, INEN |
| quality | Control calidad | ARCSA |
| fleet | Vehículos | Transporte |
| purchase | Compras | Importaciones |
| sale | Ventas | Exportaciones |

### 10.2 New Models Required

| Model | Purpose |
|:------|:--------|
| l10n_ec.guia.remision | Electronic waybill |
| l10n_ec.customs.import | DAU/Import |
| l10n_ec.customs.export | DAE/Export |
| l10n_ec.product.inen | INEN standards |
| l10n_ec.product.arcsa | ARCSA registrations |

---

**END OF DOCUMENT**
