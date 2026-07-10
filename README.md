# 🇪🇨 Localización Ecuador para Odoo 18

<div align="center">

[![License: LGPL-3](https://img.shields.io/badge/Licencia-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-purple.svg)](https://www.odoo.com)
[![SRI](https://img.shields.io/badge/SRI-Probado%20en%20Pruebas-yellow.svg)](https://sri.gob.ec)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow.svg)](https://python.org)

**Fork de producción de la localización Ecuador para Odoo 18 — ver "Estado real" antes de instalar**

[Estado Real](#-estado-real-de-este-fork-leer-antes-de-usar) •
[Instalación](#-instalación) •
[Módulos](#-módulos) •
[Historial de Correcciones](#-historial-de-correcciones-reales) •
[Documentación](#-documentación)

</div>

---

## 🏢 Desarrollado por

<div align="center">

Código original: **[Somatech.dev](https://somatech.dev)** ([`somatechlat/odoo_saas_ecuador`](https://github.com/somatechlat/odoo_saas_ecuador))

Este fork — auditoría, corrección de bugs y verificación end-to-end contra el SRI:
**[egejo](https://github.com/egejo)** ([`egejo/odoo_saas_ecuador`](https://github.com/egejo/odoo_saas_ecuador))

</div>

---

## ⚠️ Estado real de este fork (leer antes de usar)

Este es un **fork duro** del repositorio original de Somatech.dev, mantenido para un
despliegue de producción específico (Odoo 18 CE, empresa única en Ecuador — ver
[`egejo/odooCE-V18`](https://github.com/egejo/odooCE-V18), el repo de infraestructura
que consume este fork vía `git-aggregator`, pinneado por SHA).

**Por qué existe este fork**: al evaluar el repositorio original para producción
(2026-07-05), la tabla de "✅ Cumple" de este mismo README no correspondía con el
código real. Cosas que decían estar implementadas y "certificadas" no funcionaban en
absoluto la primera vez que se probaron de verdad — no en una revisión de código, sino
al instalar, transmitir contra el SRI real y leer la respuesta:

- La firma XAdES-BES era **criptográficamente inválida** (bug de canonicalización c14n
  al usar namespace por defecto en vez de prefijos `ds:`/`etsi:`) — ninguna factura
  firmada con el código original habría sido aceptada nunca por el SRI.
- El certificado `.p12` ni siquiera se **deserializaba** (bug de tipos `str`/`bytes`).
- **Nota de Crédito no estaba implementada**: `action_send_sri` renderizaba siempre el
  XML de factura sin importar el tipo de documento — la primera NC real habría chocado
  contra la factura original en el SRI.
- **Nota de Débito no existía en absoluto.**
- El modelo de **Retenciones estaba triplicado** (tres implementaciones paralelas,
  vocabularios de tipo de impuesto incompatibles entre sí) y **ninguna de las tres
  funcionaba** — el wizard de creación fallaba siempre por un dominio que nunca
  encontraba resultados.
- El catálogo de códigos de retención (renta/IVA/ISD) tenía **códigos reales
  equivocados desde el día 1** (ej. código 312 con 1.75% cuando el SRI exige 2%; los
  códigos "RIMPE" 332B/343A ni siquiera correspondían a RIMPE, sino a otros conceptos
  tributarios sin relación) y **el tipo ISD no tenía ni un solo código cargado** —
  imposible crear una retención ISD en la práctica, no solo con el código equivocado.
- El régimen RIMPE de la propia compañía (leyenda obligatoria "CONTRIBUYENTE RÉGIMEN
  RIMPE" en el XML) **no existía en absoluto**, pese a que el README lo listaba como
  soportado.
- Bugs de empaquetado bloqueaban la instalación (dependencias faltantes de
  `purchase`/`mail`/`portal`, catálogos de provincias/países duplicados, claves de
  `ir.config_parameter` colisionando entre módulos, permisos de acceso faltantes por
  completo para el modelo de retenciones).

**Desde entonces, cada módulo que se ha probado de verdad en este fork — no solo
leído — ha tenido al menos un bug real.** Ese es el criterio de trabajo de este fork:
nada se marca como funcional solo porque el código "se ve bien" o porque el manifest
lo dice; se marca funcional cuando se probó con datos reales y, cuando aplica, se
transmitió contra el servicio de pruebas/certificación real del SRI
(`celcer.sri.gob.ec`) y se recibió `AUTORIZADO`.

### ✅ Lo que sí está probado de verdad (AUTORIZADO contra el SRI real)

- Factura, Nota de Crédito, Nota de Débito y Comprobante de Retención — el ciclo
  completo firma → transmisión SOAP → autorización.
- El catálogo completo de códigos de retención: los 9 códigos de renta auditados
  contra la Resolución NAC-DGERCGC26-00000009 (312, 322, 343, 343B, 332, 343A, 319,
  344A, 304, 3440) y los 7 códigos de IVA (30/70/100/0%-en-cero/0%-no-procede/10/20/50%).
- Retención a proveedor clasificado RIMPE (código sugerido automáticamente) y régimen
  RIMPE de la propia compañía (leyenda en XML/RIDE).
- Importador de XML de proveedor (factura recibida) hacia un vendor bill en borrador —
  funcionalidad que ni siquiera existe en el módulo oficial de Enterprise.
- **Guía de Remisión** (`l10n_ec_delivery_guide`, implementada desde cero
  2026-07-10 — tampoco existe en el módulo oficial de Enterprise): múltiples guías
  desde un mismo despacho/transferencia interna, emisión con el despacho ya aprobado,
  anexo de números de serie/lote (exigido por el Art. 19 núm. 2 del Reglamento de
  Comprobantes de Venta), vínculo `docSustento` con la venta/factura que motiva el
  traslado, anulación dentro del plazo, y transportista tanto cédula como RUC — todo
  AUTORIZADO contra el SRI real.

### ⚠️ Lo que está instalado pero SIN probar con datos reales

ATS/Formulario 104, ICE, Impuesto a la Renta (tabla progresiva), Activos Fijos, Punto
de Venta, Aduanas, Nómina completa (IESS/décimos/utilidades/préstamos/vacaciones),
retención a proveedor genuinamente extranjero contra el SRI real, retención de ISD
(catálogo ya cargado, nunca transmitido — no hay un caso de uso doméstico realista para
probarlo). Instalan y cargan sin error, pero eso no es lo mismo que "funciona" según el
criterio de este fork.

### ❌ Lo que no está implementado (pese a lo que decía este README antes)

Reporte de Utilidades en `l10n_ec_sut` (placeholder vacío en el código).

Ver [`CLAUDE.md`](../../CLAUDE.md) del repo de infraestructura para el detalle completo,
checkpoint por checkpoint, de cada bug encontrado y corregido.

---

## ⚡ Características Principales

### 📄 Facturación Electrónica SRI

| Característica | Estado real |
|----------------|--------|
| Firma digital XAdES-BES (SHA-256) | ✅ Corregida y verificada con `signxml` contra un certificado real |
| Factura, Nota de Crédito, Nota de Débito, Comprobante de Retención | ✅ AUTORIZADO end-to-end contra SRI Pruebas |
| Guía de Remisión (múltiples guías/despacho, anexo series, docSustento, anulación) | ✅ Implementada 2026-07-10, AUTORIZADO end-to-end |
| Generación RIDE PDF | ✅ Rediseñado con bordes, forma de pago e info adicional |
| Clave de acceso 49 dígitos (Módulo 11) | ✅ |
| Importador de XML de proveedor → vendor bill borrador | ✅ Feature propia de este fork, no existe en Enterprise |

### 💰 Cumplimiento Tributario

| Regulación | Estado real |
|------------|----------------|
| Catálogo de retención Renta (9 códigos auditados NAC-DGERCGC26-00000009) | ✅ Auditado y AUTORIZADO |
| Catálogo de retención IVA (7 códigos, Ficha Técnica SRI) | ✅ Auditado y AUTORIZADO |
| Catálogo de retención ISD (código 4580) | ⚠️ Cargado, sin transmitir (sin caso de uso doméstico) |
| Régimen RIMPE (compañía + proveedor) | ✅ Implementado y AUTORIZADO 2026-07-09 |
| Límite Consumidor Final $50 / Anulación 7 días | ⚠️ Implementado, sin probar en producción real |
| ATS / Formulario 104 | ⚠️ Instalado, generación real sin probar |

### 👥 Nómina IESS 2026

Instalado (IESS, décimos, vacaciones, préstamos, portal empleado) pero **sin ningún
empleado ni contrato real configurado todavía** — nada de esta sección se ha probado
con datos reales. Ver checklist en `CLAUDE.md`.

---

## 📦 Módulos (20 Total — corregido; el README original decía 19, faltaba contar `l10n_ec`)

Los que este fork ha probado de verdad quedan marcados ✅; el resto — instalado,
carga sin error, sin ejercitar con datos reales — queda ⚠️.

### Módulos Base (Obligatorios)

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `l10n_ec` | Configuración empresa, wizard setup, datos Ecuador | ✅ |
| `l10n_ec_base` | Plan de cuentas NEC, validación RUC/Cédula, catálogo de países SRI | ✅ |
| `l10n_ec_edi` | Generación XML, firma XAdES-BES, clave de acceso | ✅ Firma corregida y verificada |
| `l10n_ec_sri` | Integración SOAP con SRI (pruebas/producción) | ✅ AUTORIZADO en pruebas |

### Módulos Contables

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `l10n_ec_withholding` | Retenciones IR + IVA + ISD | ✅ Modelo consolidado, catálogo auditado, AUTORIZADO |
| `l10n_ec_rimpe` | Régimen RIMPE emprendedores/populares | ✅ Implementado y AUTORIZADO 2026-07-09 |
| `l10n_ec_income_tax` | Impuesto a la renta, gastos personales | ⚠️ Sin probar con empleado real |
| `l10n_ec_ice` | Impuesto Consumos Especiales | ⚠️ Sin probar con producto real |
| `l10n_ec_reports` | ATS, Formulario 104 | ⚠️ Sin probar generación real |

### Módulos HR/Nómina

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `l10n_ec_hr_payroll` | IESS, Décimos, SBU | ⚠️ Sin empleados/contratos configurados |
| `l10n_ec_vacation` | Libro de vacaciones, control días | ⚠️ Sin probar contra caso real |
| `l10n_ec_sut` | Reportes MDT (Décimos) | ⚠️ Sin probar; **Utilidades no implementado** (placeholder) |
| `l10n_ec_loans` | Préstamos quirografarios/hipotecarios | ⚠️ Sin probar wizard IESS con archivo real |

### Módulos Operativos

| Módulo | Descripción | Estado |
|--------|-------------|--------|
| `l10n_ec_delivery_guide` | Guía de Remisión electrónica (reemplaza a `l10n_ec_stock`) | ✅ Implementada y AUTORIZADO 2026-07-10 |
| `l10n_ec_pos` | Facturación electrónica en POS | ⚠️ Sin ningún punto de venta configurado |
| `l10n_ec_customs` | DAU, partidas arancelarias, FODINFA, ISD | ⚠️ Sin probar con importación real |
| `l10n_ec_quality` | Control calidad productos Ecuador | ⚠️ Solo aplica si la empresa fabrica |
| `l10n_ec_asset` | Activos fijos depreciación Ecuador | ⚠️ Sin probar con activo real |
| `l10n_ec_bank_transfer` | Transferencias bancarias Ecuador | ⚠️ Sin probar generación real de TXT |
| `l10n_ec_portal` | Portal cliente/proveedor Ecuador | ⚠️ Sin usuario de portal creado todavía |

---

## 🚀 Instalación

### En esta instancia de producción (recomendado si vienes desde `egejo/odooCE-V18`)

Este fork se consume vía `git-aggregator`, pinneado por SHA (no por rama), desde
`scripts/repos.yaml` del repo de infraestructura:

```yaml
addons/somatechlat:
  remotes:
    egejo_fork: git@github.com-odooCE-ec-edi:egejo/odoo_saas_ecuador.git
  target: egejo_fork main
  merges:
    - egejo_fork <SHA_actual_en_repos.yaml>
```

```bash
pipx install git-aggregator
gitaggregate -c scripts/repos.yaml
```

Solo se montan en `addons_path` los módulos `l10n_ec_base`, `l10n_ec_edi`,
`l10n_ec_sri`, `l10n_ec_withholding`, `l10n_ec_rimpe`, `l10n_ec_delivery_guide` y el
resto de módulos fiscales/operacionales listados arriba — **nunca** `l10n_ec`, que
choca de nombre técnico con el core de Odoo. El antiguo `l10n_ec_stock` (mismo
problema de colisión) fue eliminado de este fork y reemplazado por
`l10n_ec_delivery_guide` (ver Historial de Correcciones).

### Requisitos Previos

- **Odoo 18** Community o Enterprise
- **Python 3.10+**
- **PostgreSQL 15+**
- **Certificado digital SRI** (formato .p12) — nota: si el certificado viene cifrado
  con PKCS12 RC2-40-CBC (común en certificados Security Data/Banco Central/ANF), el
  contenedor necesita el provider "legacy" de OpenSSL activado, ver `CLAUDE.md`.

### Instalación genérica (fuera de este despliegue)

```bash
# 1. Clonar este fork (no el repositorio original de Somatech.dev)
git clone https://github.com/egejo/odoo_saas_ecuador.git

# 2. Instalar dependencias Python
pip install -r requirements.txt

# 3. Copiar a directorio de addons de Odoo
cp -r l10n_ec_* /ruta/a/odoo/addons/

# 4. Reiniciar Odoo y actualizar lista de módulos
./odoo-bin -d mi_base_datos -u all

# 5. Instalar módulo base
# Desde Odoo: Aplicaciones > Buscar "Ecuador" > Instalar
```

📖 Ver [Guía de Instalación](docs/INSTALACION.md) — **nota**: este documento viene del
repositorio original y no ha sido re-auditado junto con el código; puede seguir
describiendo funcionalidad de forma más optimista que la sección "Estado real" de
arriba. Ante cualquier discrepancia, confiar en este README y en `CLAUDE.md`.

---

## ⚙️ Configuración

### 1. Datos de Empresa

**Configuración > Empresas > Su Empresa**

- RUC (13 dígitos)
- Razón Social
- Dirección fiscal
- Régimen Tributario (General / RIMPE) — pestaña "Ecuador SRI"

### 2. Certificado Digital

**Contabilidad > Configuración > Ecuador SRI > Certificados**

1. Subir archivo .p12
2. Ingresar contraseña
3. Activar certificado

### 3. Ambiente SRI

**Configuración > Empresas > Ecuador SRI**

- **Pruebas**: `celcer.sri.gob.ec` (default de este fork — cambiar a producción
  requiere revisión explícita, ver Reglas de Seguridad en `CLAUDE.md`)
- **Producción**: `cel.sri.gob.ec`

---

## 📚 Documentación

| Documento | Descripción |
|-----------|-------------|
| [📥 Instalación](docs/INSTALACION.md) | Del repo original, sin re-auditar (ver nota arriba) |
| [📖 Manual de Usuario](docs/MANUAL_USUARIO.md) | Del repo original, sin re-auditar |
| [📋 Cumplimiento Regulatorio](docs/CUMPLIMIENTO_REGULATORIO.md) | Del repo original, sin re-auditar |
| Historial real de correcciones | Ver sección de abajo, y `CLAUDE.md` del repo de infraestructura |

---

## 📜 Historial de Correcciones Reales

Resumen de las sesiones de auditoría/corrección de este fork (33 commits propios sobre
78 totales del historial). Detalle completo, con SHAs exactos y el razonamiento de cada
fix, en `CLAUDE.md` del repo `egejo/odooCE-V18`.

- **2026-07-05** — Empaquetado: dependencias faltantes (`purchase`, `mail`, `portal`),
  catálogos duplicados, `view_mode="tree"`→`"list"` (Odoo 18). **Firma XAdES-BES**:
  corregida de criptográficamente inválida a verificada con `signxml`. **Nota de
  Crédito**: implementada desde cero (no existía). Factura y NC confirmadas AUTORIZADO
  contra SRI Pruebas por primera vez.
- **2026-07-06/07** — RIDE rediseñado (bordes, forma de pago, info adicional, envío por
  correo con XML+PDF según Art. 6 Res. NAC-DGERCGC18-00000233). **Nota de Débito**
  implementada desde cero. **Retenciones consolidadas**: de 3 modelos paralelos
  rotos a 1 funcional (`account.retention`), con XML reescrito contra el schema real.
  Bug sistémico de catálogo de tipos de documento duplicado (rompía "Send to SRI" con
  un `ValueError` real en producción) encontrado y corregido.
- **2026-07-08** — Importador de XML de proveedor (feature nueva, no en Enterprise).
  Bug de RUC real clasificado como "exterior" corregido. `tipoSujetoRetenido` para
  proveedor extranjero implementado. Catálogo de países SRI cargado (241 países).
  **Auditoría completa de las 3 tablas de retención** (renta/IVA/ISD) contra
  documentación oficial del SRI — 4+ códigos reales equivocados desde el día 1
  corregidos, varios códigos que ni existían agregados.
- **2026-07-09** — Bug de zona horaria corregido (fechas calculadas en UTC en vez de
  hora Ecuador, causaban rechazo real del SRI cerca de medianoche). **RIMPE
  implementado de verdad**: régimen de compañía (no existía) y código de retención de
  proveedor (existía con códigos equivocados sin usar en ningún lado desde el día 1,
  ahora corregido y conectado al wizard). Los 9 códigos de retención renta y los 7 de
  IVA confirmados **AUTORIZADO** contra el SRI real, uno por uno.
- **2026-07-10** — **Guía de Remisión implementada desde cero** (nuevo módulo
  `l10n_ec_delivery_guide`, reemplazando por completo el `l10n_ec_stock` heredado del
  upstream que nunca se instaló ni se probó por chocar de nombre técnico con el core de
  Odoo — y que además tenía bugs reales: RUC del transportista mal mapeado a su número
  de licencia, motivo de traslado ilegible, sin bloque `docSustento`, sin RIDE/correo/
  anulación). Diseño con relación N:1 hacia `stock.picking` (permite varias guías por
  despacho) sin restricción de estado (se puede emitir con el despacho ya aprobado), más
  anexo de números de serie/lote por línea. Probado end-to-end contra el SRI real en
  varias rondas: transferencia interna con 2 guías y producto con número de serie;
  vínculo `docSustento` con una venta real facturada y autorizada (encontrado y
  corregido un bug real: `numDocSustento` debe conservar los guiones, patrón distinto
  al de retenciones); anulación de una guía autorizada (guard de plazo probado en ambos
  sentidos); transportista tipo RUC además de cédula. Todos los casos **AUTORIZADO**.

---

## 🏛️ Cumplimiento Regulatorio

| Entidad | Regulación | Estado real |
|---------|------------|--------|
| **SRI** | Facturación Electrónica (Factura/NC/ND/Retención) | ✅ AUTORIZADO en Pruebas |
| **SRI** | Catálogo de retenciones NAC-DGERCGC26-00000009 | ✅ Auditado y AUTORIZADO |
| **SRI** | Régimen RIMPE | ✅ AUTORIZADO |
| **SRI** | Guía de Remisión | ✅ Implementada y AUTORIZADO 2026-07-10 |
| **SRI** | ATS / Formulario 104 | ⚠️ Instalado, sin probar |
| **IESS** | Aportes, Décimos | ⚠️ Instalado, sin empleados reales |
| **SENAE** | FODINFA, IVA importación, ISD | ⚠️ Instalado, sin importación real |
| **SUPERCIAS** | Estados financieros NIIF | ⚠️ No auditado en este fork |

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! El criterio de aceptación de este fork es
sencillo: **si no se probó de verdad (idealmente contra el SRI real), no se documenta
como funcional.**

1. Fork de [`egejo/odoo_saas_ecuador`](https://github.com/egejo/odoo_saas_ecuador)
2. Crear rama: `git checkout -b feature/mi-mejora`
3. Commit: `git commit -m "Añade mi mejora"`
4. Push: `git push origin feature/mi-mejora`
5. Abrir Pull Request, describiendo cómo se probó (no solo que "se ve bien")

📖 Ver [Guía de Contribución](CONTRIBUIR.md)

---

## 📄 Licencia

Este proyecto está licenciado bajo **LGPL-3.0** - ver archivo [LICENSE](LICENSE).

```
Copyright 2026 Somatech.dev (código original)
Copyright 2026 egejo (correcciones, auditoría y funcionalidad nueva de este fork)
License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0)
```

---

## 🆘 Soporte

Este es un fork mantenido para un despliegue de producción específico, no un producto
comercial con soporte dedicado.

| Canal | Contacto |
|-------|----------|
| 🐛 Issues de este fork | [GitHub Issues](https://github.com/egejo/odoo_saas_ecuador/issues) |
| 📦 Repositorio original (Somatech.dev) | [somatechlat/odoo_saas_ecuador](https://github.com/somatechlat/odoo_saas_ecuador) |

---

<div align="center">

**Hecho con ❤️ en Ecuador 🇪🇨 — y con bastante tiempo probando contra el SRI real**

</div>
