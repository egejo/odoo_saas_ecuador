/** @odoo-module **/

/**
 * Ecuador POS SRI Integration - OWL Module Entry Point
 * Provides SRI electronic receipt generation for Point of Sale
 */

import { registry } from "@web/core/registry";

const posL10nEcCategory = registry.category("pos_l10n_ec_sri");

export const posL10nEcSRI = {
    name: "Ecuador SRI POS",
    version: "18.0.1.0.0",
};
