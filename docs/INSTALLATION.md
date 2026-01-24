# Installation Guide

## Prerequisites

- **Odoo 18** Community or Enterprise
- **Python 3.10+**
- **PostgreSQL 15+**
- **SRI Digital Certificate** (.p12 format)

## Python Dependencies

```bash
pip install zeep cryptography lxml requests
```

## Installation Methods

### Method 1: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/somatechlat/odoo_saas_ecuador.git

# Add to docker-compose.yml volumes
volumes:
  - ./odoo_saas_ecuador:/mnt/extra-addons

# Set addons path in odoo.conf
addons_path = /mnt/extra-addons,/mnt/addons

# Restart container
docker-compose restart odoo
```

### Method 2: Source Installation

```bash
# Clone to Odoo addons directory
cd /path/to/odoo/addons
git clone https://github.com/somatechlat/odoo_saas_ecuador.git

# Or copy modules individually
cp -r l10n_ec_* /path/to/odoo/addons/

# Update Odoo configuration
addons_path = /path/to/odoo/addons
```

### Method 3: Odoo.sh

1. Add repository to `odoo.sh` project settings
2. Repository URL: `https://github.com/somatechlat/odoo_saas_ecuador.git`
3. Deploy branch

## Module Installation Order

Install modules in this order:

1. **l10n_ec_base** (required first)
2. **l10n_ec_edi** (electronic invoicing)
3. **l10n_ec_sri** (SRI integration)
4. **Other modules** as needed

```bash
# Via command line
./odoo-bin -d your_database -i l10n_ec_base,l10n_ec_edi,l10n_ec_sri
```

## Configuration

### 1. Company Setup

Go to **Settings > Companies** and configure:

- **RUC**: 13-digit tax ID (automatically validated)
- **Legal Name**: As registered with SRI
- **Address**: Ecuador address

### 2. Certificate Upload

Go to **Accounting > Configuration > Ecuador SRI > Certificates**:

1. Click **Create**
2. Upload `.p12` certificate file
3. Enter certificate password
4. Set expiration date
5. Activate certificate

### 3. Environment Selection

Go to **Settings > Companies > Ecuador SRI**:

- **Test (Pruebas)**: Development/testing
- **Production (Producción)**: Live SRI transmission

### 4. Emission Points

Configure in **Accounting > Configuration > Ecuador SRI > Emission Points**:

- Establishment code (001)
- Emission point code (001)
- Assigned sequences

## Verification

### Test Connection

1. Create a test invoice
2. Click **Send to SRI** button
3. Check SRI response

### Expected Response

- **RECIBIDA**: Document received, awaiting authorization
- **AUTORIZADO**: Successfully authorized
- **RECHAZADO**: Rejected (check error message)

## Troubleshooting

### Certificate Errors

| Error | Solution |
|-------|----------|
| Invalid password | Verify .p12 password |
| Expired certificate | Renew with authorized provider |
| Certificate not active | Check expiration date |

### SRI Connection Errors

| Error | Solution |
|-------|----------|
| Connection timeout | Check internet connectivity |
| Service unavailable | SRI maintenance (try later) |
| Invalid RUC | Verify company RUC format |

### Common Issues

1. **Module not found**: Verify addons_path includes module directory
2. **Dependency error**: Install modules in correct order
3. **Python packages missing**: Run `pip install` for dependencies

## Support

For technical support:
- GitHub Issues: https://github.com/somatechlat/odoo_saas_ecuador/issues
- Email: soporte@somatech.dev

---

**License**: LGPL-3.0 | **Developed by**: [Somatech.dev](https://somatech.dev)
