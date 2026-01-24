# Guía de Contribución

## ¡Bienvenido! 👋

Gracias por considerar contribuir al proyecto de Localización Ecuador para Odoo. Este documento describe el proceso para contribuir.

---

## Código de Conducta

- Ser respetuoso e inclusivo
- Enfocarse en retroalimentación constructiva
- Ayudar a mantener una comunidad acogedora

---

## Cómo Contribuir

### Reportar Errores

1. Verificar si el error ya fue reportado
2. Crear un nuevo issue con:
   - Título claro
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Versión de Odoo
   - Versión del módulo

### Sugerir Mejoras

1. Abrir un issue con prefijo `[Mejora]`
2. Describir el caso de uso
3. Explicar el requisito regulatorio (si aplica)

### Enviar Código

1. **Fork** del repositorio
2. **Crear rama**: `git checkout -b feature/mi-mejora`
3. **Seguir estándares** (ver abajo)
4. **Probar** los cambios
5. **Commit** con mensajes claros
6. **Push** a tu fork
7. **Abrir Pull Request**

---

## Estándares de Código

### Guías OCA

Seguimos los [Estándares de Código OCA](https://github.com/OCA/maintainer-tools/blob/master/CONTRIBUTING.md):

- PEP8 para Python
- Docstrings claros
- Nombres de variables significativos

### Requisitos de Manifest

```python
{
    'author': 'Tu Nombre, Somatech.dev, Odoo Community Association (OCA)',
    'website': 'https://github.com/somatechlat/odoo_saas_ecuador',
    'license': 'LGPL-3',
    # ...
}
```

### Encabezado de Copyright

Todos los archivos Python deben incluir:

```python
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#
# Copyright 2026 Tu Nombre
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
```

### Mensajes de Commit

```
[MODULO] Descripción corta (máx 72 caracteres)

Explicación más larga si es necesario.

Fixes #123
```

---

## Pruebas

- Agregar pruebas unitarias para nuevas funcionalidades
- Asegurar que las pruebas existentes pasen
- Probar con CE y EE si es posible

---

## Proceso de Revisión

1. Todos los PR requieren al menos una revisión
2. Las verificaciones de CI deben pasar
3. Sin conflictos de merge
4. Documentación actualizada si es necesario

---

## Licencia

Al contribuir, aceptas que tus contribuciones serán licenciadas bajo LGPL-3.0.

---

## ¿Preguntas?

Contacto: soporte@somatech.dev
