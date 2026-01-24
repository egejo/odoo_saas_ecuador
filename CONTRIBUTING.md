# Contributing Guidelines

## Welcome!

Thank you for considering contributing to the Odoo Ecuador Localization project. This document outlines the process for contributing.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Help maintain a welcoming community

## How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Create a new issue with:
   - Clear title
   - Steps to reproduce
   - Expected vs actual behavior
   - Odoo version
   - Module version

### Suggesting Features

1. Open an issue with `[Feature]` prefix
2. Describe the use case
3. Explain the regulatory requirement (if applicable)

### Submitting Code

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature`
3. **Follow coding standards** (see below)
4. **Test** your changes
5. **Commit** with clear messages
6. **Push** to your fork
7. **Open a Pull Request**

## Coding Standards

### OCA Guidelines

We follow [OCA Coding Standards](https://github.com/OCA/maintainer-tools/blob/master/CONTRIBUTING.md):

- PEP8 for Python
- Clear docstrings
- Meaningful variable names

### Manifest Requirements

```python
{
    'author': 'Your Name, Somatech.dev, Odoo Community Association (OCA)',
    'website': 'https://github.com/somatechlat/odoo_saas_ecuador',
    'license': 'LGPL-3',
    # ...
}
```

### Copyright Header

All Python files must include:

```python
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Your Name
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
```

### Commit Messages

```
[MODULE] Short description (max 72 chars)

Longer explanation if needed.

Fixes #123
```

## Testing

- Add unit tests for new features
- Ensure existing tests pass
- Test with both CE and EE if possible

## Review Process

1. All PRs require at least one review
2. CI checks must pass
3. No merge conflicts
4. Documentation updated if needed

## License

By contributing, you agree that your contributions will be licensed under LGPL-3.0.

---

**Questions?** Contact: soporte@somatech.dev
