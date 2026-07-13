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
 *
 * Por normativa, TODA venta debe quedar facturada (no es una opcion del
 * cajero) -- por eso is_to_invoice() se fuerza a true, y el cliente por
 * defecto (Consumidor Final) se preselecciona en cada orden nueva. El
 * boton nativo "Invoice"/"Facturar" de Odoo, si se deja tal cual, dispara
 * SU PROPIO mecanismo (factura y descarga el PDF de inmediato, sin
 * esperar la autorizacion del SRI -- por eso se veia "DOCUMENTO NO
 * AUTORIZADO (DRAFT)"): shouldDownloadInvoice() se desactiva aqui para
 * que ese camino nunca compita con el de este modulo.
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
    setup(vals) {
        super.setup(...arguments);
        // Preselecciona Consumidor Final en toda orden nueva sin cliente:
        // la mayoria de ventas de mostrador no identifican al comprador,
        // y facturar (obligatorio) requiere un partner en la orden.
        if (
            this.state === "draft" &&
            !this.partner_id &&
            this.config?.l10n_ec_sri_active &&
            this.config?.l10n_ec_default_partner_id
        ) {
            this.set_partner(this.config.l10n_ec_default_partner_id);
        }
    },

    // Por normativa la factura no es opcional: se ignora el valor
    // guardado y se fuerza siempre a true (el boton "Invoice" del pago
    // sigue siendo clickeable pero deja de tener efecto real).
    is_to_invoice() {
        if (this.config?.l10n_ec_sri_active) {
            return true;
        }
        return super.is_to_invoice(...arguments);
    },

    export_for_printing(baseUrl, headerData) {
        const result = super.export_for_printing(...arguments);
        result.l10n_ec_sri = this.l10n_ec_sri_receipt_data || null;
        return result;
    },
});

patch(PaymentScreen.prototype, {
    // Evita que el flujo nativo de Odoo (descargar el PDF de la factura
    // apenas se crea, sin esperar autorizacion del SRI) compita con el
    // de este modulo -- _l10n_ec_invoiceAndWaitForSri es quien maneja
    // facturacion + espera + impresion del ticket de aqui en adelante.
    shouldDownloadInvoice() {
        if (this.pos.config.l10n_ec_sri_active) {
            return false;
        }
        return super.shouldDownloadInvoice(...arguments);
    },

    async afterOrderValidation() {
        try {
            await this._l10n_ec_invoiceAndWaitForSri();
        } catch (error) {
            // Defensa extra: bajo ninguna circunstancia un error aqui debe
            // dejar la pantalla del POS colgada sin pasar al recibo.
            console.error("l10n_ec_pos: error inesperado facturando/transmitiendo al SRI", error);
        }
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
