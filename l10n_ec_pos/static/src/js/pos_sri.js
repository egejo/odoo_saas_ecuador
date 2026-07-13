/** @odoo-module **/

/**
 * Ecuador POS SRI Integration.
 *
 * El ticket de rollo que imprime el POS es, para efectos del SRI, una
 * Representacion Impresa del Documento Electronico (RIDE) en formato
 * reducido -- no un "ticket de caja registradora" generico (esos dejaron
 * de ser validos en Ecuador desde 2018, salvo zonas sin conectividad).
 * Para que sea valida necesita los mismos datos obligatorios que la
 * factura completa: emisor, receptor, tipo/numero de comprobante, fecha,
 * numero de autorizacion y clave de acceso (con codigo de barras).
 *
 * Esto solo es posible si la orden ya esta facturada y autorizada por el
 * SRI antes de imprimir. Por eso, al validar el pago, se factura y
 * transmite la orden de inmediato (tiempo real, como exige la normativa
 * vigente desde 2026), y se espera aqui -- del lado del navegador, sin
 * bloquear ningun worker de Odoo -- a que el SRI la autorice antes de
 * imprimir el ticket.
 */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

const SRI_POLL_INTERVAL_MS = 3000;
const SRI_POLL_MAX_TRIES = 6; // ~18s, en linea con lo observado contra el SRI de pruebas

function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}

patch(PosOrder.prototype, {
    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        result.l10n_ec_sri = this.l10n_ec_sri_receipt_data || null;
        return result;
    },
});

patch(PaymentScreen.prototype, {
    async afterOrderValidation() {
        await this._l10n_ec_invoiceAndWaitForSri();
        return super.afterOrderValidation(...arguments);
    },

    async _l10n_ec_invoiceAndWaitForSri() {
        const order = this.currentOrder;
        if (!this.pos.config.l10n_ec_sri_active || !order || typeof order.id !== "number") {
            // Orden todavia no sincronizada (sin id numerico real) o SRI
            // desactivado para este POS: no hay nada que facturar aqui.
            return;
        }

        this.env.services.ui.block();
        try {
            let result = await this.pos.data.call(
                "pos.order",
                "l10n_ec_pos_invoice_and_send",
                [order.id]
            );

            if (result && result.l10n_ec_sri_status === "sent") {
                for (let i = 0; i < SRI_POLL_MAX_TRIES; i++) {
                    await sleep(SRI_POLL_INTERVAL_MS);
                    result = await this.pos.data.call(
                        "pos.order",
                        "l10n_ec_pos_check_sri",
                        [order.id]
                    );
                    if (["authorized", "rejected"].includes(result.l10n_ec_sri_status)) {
                        break;
                    }
                }
            }

            order.l10n_ec_sri_receipt_data = result || null;

            if (result && result.l10n_ec_sri_status === "rejected") {
                this.dialog.add(AlertDialog, {
                    title: _t("SRI rechazo la factura"),
                    body: result.l10n_ec_sri_error || _t("Motivo no especificado."),
                });
            } else if (result && result.l10n_ec_sri_status === "sent") {
                this.dialog.add(AlertDialog, {
                    title: _t("SRI: autorizacion pendiente"),
                    body: _t(
                        "El SRI no autorizo el comprobante a tiempo. La venta quedo " +
                        "registrada; reintente el envio desde Contabilidad > Facturas " +
                        "(%(name)s) antes de entregar un comprobante al cliente.",
                        { name: result.move_name || "" }
                    ),
                });
            }
        } catch (error) {
            // No se pudo ni siquiera facturar (ej. sin certificado activo,
            // sin conexion al SRI). No se bloquea la venta -- ya esta
            // pagada y sincronizada -- pero se avisa claramente al cajero.
            this.dialog.add(AlertDialog, {
                title: _t("No se pudo facturar ante el SRI"),
                body: error && error.data && error.data.message
                    ? error.data.message
                    : _t("Revise Contabilidad > Facturas para completar la factura a mano."),
            });
        } finally {
            this.env.services.ui.unblock();
        }
    },
});
