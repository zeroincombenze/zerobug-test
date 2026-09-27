/** @odoo-module **/
/* Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
 * License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
 *
 * VERSION-DEPENDENT: Odoo 16 adapter, [?] button in the control panel.
 */
import {ControlPanel} from "@web/search/control_panel/control_panel";
import {patch} from "@web/core/utils/patch";
import {useService} from "@web/core/utils/hooks";
import {onMounted} from "@odoo/owl";

patch(ControlPanel.prototype, "web_context_help.ControlPanel", {
    setup() {
        this._super(...arguments);
        this.contextHelp = useService("context_help");
        onMounted(() => {
            // Dialogs (e.g. Search More) keep the help of the main view
            if (!this.env.inDialog) {
                this.contextHelp.notify(this.getContextHelpContext());
            }
        });
    },
    getContextHelpContext() {
        const config = this.env.config || {};
        return {
            model:
                (this.env.searchModel && this.env.searchModel.resModel) ||
                (this.env.model && this.env.model.root && this.env.model.root.resModel),
            viewType: config.viewType,
            viewId: config.viewId,
        };
    },
    onContextHelpClick() {
        this.contextHelp.open(this.getContextHelpContext());
    },
});
