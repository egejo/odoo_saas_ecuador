import { Component, onMounted, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

/**
 * Pone el foco inicial en el número de identificación de un contacto nuevo.
 *
 * En Ecuador el nombre no se teclea: se trae del catastro del SRI
 * escribiendo la cédula o el RUC, así que abrir con el cursor en el nombre
 * (lo que hace la vista base de Odoo) invierte el orden real de trabajo.
 *
 * No se puede hacer con `default_focus` en la vista: el motor de
 * formularios localiza ese campo por su `id` en el DOM, y `vat` usa el
 * widget `field_partner_autocomplete`, que renderiza su propio input sin
 * ese id; el foco caía siempre al primer input de la página por el camino
 * de respaldo del renderer.
 */
export class L10nEcVatAutofocus extends Component {
    static template = "l10n_ec_base.VatAutofocus";
    static props = { ...standardWidgetProps };

    setup() {
        this.root = useRef("root");
        onMounted(() => {
            if (!this.props.record.isNew) {
                return;
            }
            // El propio renderer del formulario enfoca su campo por defecto
            // en un efecto del componente padre, que corre DESPUÉS del
            // montaje de este hijo: sin esperar al siguiente cuadro nos
            // devolvería el foco al nombre.
            requestAnimationFrame(() => {
                const form = this.root.el?.closest(".o_form_renderer");
                const input = form?.querySelector('[name="vat"] input');
                if (input && !input.value) {
                    input.focus();
                }
            });
        });
    }
}

registry.category("view_widgets").add("l10n_ec_vat_autofocus", {
    component: L10nEcVatAutofocus,
});

/**
 * Botón "Consultar datos" de la ficha de contacto.
 *
 * Antes era un `<button type="object">` que llamaba a
 * `action_load_from_sri`. Funcionaba, pero en Odoo TODO botón de tipo
 * objeto graba el registro antes de ejecutarse, y la ficha que abre el POS
 * lleva un `onSave` (ver `makeActionAwaitable` en `pos_store.js`) que
 * cierra el diálogo y devuelve el cliente a la orden en cuanto se graba:
 * el cajero perdía la ventana a mitad de la carga, sin poder completar
 * correo y dirección, que la factura sí necesita.
 *
 * Este widget consulta el catastro por RPC y vuelca el resultado en el
 * formulario abierto (`record.update`), sin guardar nada: la ventana
 * queda donde estaba y el cajero graba una sola vez, al final.
 */
export class L10nEcSriLookupButton extends Component {
    static template = "l10n_ec_base.SriLookupButton";
    static props = { ...standardWidgetProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
    }

    async onClick() {
        const record = this.props.record;
        const country = record.data.country_id;
        const result = await this.orm.call("res.partner", "l10n_ec_sri_lookup", [
            record.data.vat,
            country ? country[0] : false,
        ]);
        if (result.values) {
            await record.update(result.values);
        }
        this.notification.add(result.message, {
            title: result.title,
            type: result.type,
        });
    }
}

registry.category("view_widgets").add("l10n_ec_sri_lookup", {
    component: L10nEcSriLookupButton,
});
