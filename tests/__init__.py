# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    ODOO ECUADOR LOCALIZATION TEST SUITE                       ║
║                            Somatech.dev 2026                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  tests/                                                                       ║
║  ├── __init__.py               # This file                                   ║
║  ├── unit/                     # Unit tests (Odoo TestCase)                  ║
║  │   ├── test_invoice_emission.py                                            ║
║  │   ├── test_retention.py                                                   ║
║  │   ├── test_consumidor_final.py                                            ║
║  │   └── test_sri_validation.py                                              ║
║  ├── e2e/                      # End-to-end tests (Playwright)               ║
║  │   ├── test_invoice_flow.py                                                ║
║  │   └── conftest.py                                                         ║
║  └── regulatory/               # Regulatory compliance tests                 ║
║      ├── test_sri_2026_rules.py                                              ║
║      └── test_tax_rates.py                                                   ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

from . import unit
from . import regulatory
# e2e tests run separately with pytest-playwright
