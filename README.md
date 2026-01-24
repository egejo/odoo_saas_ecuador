# 🇪🇨 Odoo Ecuador Localization (SRI 2026)

[![License: LGPL-3](https://img.shields.io/badge/License-LGPL--3-blue.svg)](https://www.gnu.org/licenses/lgpl-3.0)
[![Odoo Version](https://img.shields.io/badge/Odoo-18.0-purple.svg)](https://www.odoo.com)
[![Compliance](https://img.shields.io/badge/SRI-2026%20Certified-green.svg)](https://sri.gob.ec)

Complete Ecuadorian localization for Odoo 18, fully compliant with SRI 2026 regulations.

**Developed by [Somatech.dev](https://somatech.dev)**

---

## 📦 Modules

| Module | Description | Application |
|--------|-------------|-------------|
| `l10n_ec_base` | Chart of Accounts (NEC), RUC/Cédula validation, Tax Templates | ✅ Core |
| `l10n_ec_edi` | XML Generation, XAdES-BES Signing, Access Key | ✅ Core |
| `l10n_ec_sri` | SRI SOAP Integration (Test/Production) | ✅ Core |
| `l10n_ec_withholding` | Retenciones (IR + IVA), 5-day Rule | Accounting |
| `l10n_ec_stock` | Guía de Remisión | Inventory |
| `l10n_ec_pos` | POS Electronic Invoicing | Point of Sale |
| `l10n_ec_reports` | ATS, Form 104 | Reporting |
| `l10n_ec_hr_payroll` | IESS, Décimos, Utilidades | HR |
| `l10n_ec_customs` | DAU, Tariff Codes, FODINFA | Import/Export |

---

## ⚡ Key Features

### Electronic Invoicing (SRI 2026)
- ✅ Real-time SRI transmission (mandatory January 2026)
- ✅ XAdES-BES digital signature (SHA-256)
- ✅ All document types: Factura, NC, ND, Retención, Guía
- ✅ RIDE PDF generation
- ✅ Ficha Técnica v2.32 compliance

### Tax Compliance
- ✅ IVA 15% (código 4) - Standard 2026
- ✅ IVA 5% (código 5) - Construction
- ✅ Consumidor Final $50 limit enforcement
- ✅ 7-day invoice annulment rule
- ✅ CF invoices cannot be annulled

### Payroll (IESS 2026)
- ✅ SBU $482 (2026)
- ✅ IESS 9.45%/12.15%
- ✅ Décimo Tercero (Dec 24)
- ✅ Décimo Cuarto (Mar 15 / Aug 15)
- ✅ Utilidades 15% (Apr 15)

---

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/somatechlat/odoo_saas_ecuador.git

# Add to Odoo addons path
cp -r odoo_saas_ecuador/* /path/to/odoo/addons/

# Install Python dependencies
pip install zeep cryptography lxml requests

# Update module list in Odoo, then install l10n_ec_base
```

See [INSTALLATION.md](docs/INSTALLATION.md) for detailed instructions.

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Installation Guide](docs/INSTALLATION.md) | Step-by-step setup |
| [User Manual (ES)](docs/USER_MANUAL_ES.md) | Complete user guide in Spanish |
| [Admin Guide](docs/ADMIN_GUIDE.md) | Administration and certificates |
| [Developer Guide](docs/DEVELOPER_GUIDE.md) | API and extending modules |
| [Regulatory Reference](docs/REGULATORY_2026.md) | Current laws and rates |

---

## 📋 Regulatory Compliance

| Agency | Regulation | Status |
|--------|------------|--------|
| **SRI** | Electronic Invoicing 2026 | ✅ Compliant |
| **SRI** | Resolution NAC-DGERCGC25-00000017 | ✅ Compliant |
| **IESS** | Contribution Rates 2026 | ✅ Compliant |
| **Min. Trabajo** | SBU $482 (Acuerdo MDT-2025-195) | ✅ Compliant |
| **SENAE** | Import Taxes (FODINFA 0.5%) | ✅ Compliant |

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch
3. Follow OCA coding standards
4. Submit a pull request

---

## 📄 License

This project is licensed under **LGPL-3.0** - see the [LICENSE](LICENSE) file for details.

---

## 🏢 About

Developed and maintained by **[Somatech.dev](https://somatech.dev)** in collaboration with the **Odoo Community Association (OCA)**.

For support, contact: soporte@somatech.dev
