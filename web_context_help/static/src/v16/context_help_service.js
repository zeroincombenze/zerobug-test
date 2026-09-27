/** @odoo-module **/
/* Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
 * License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
 *
 * VERSION-DEPENDENT: Odoo 16 adapter (OWL services).
 * Opens the help window and serves its postMessage requests.
 */
import {registry} from "@web/core/registry";
import {browser} from "@web/core/browser/browser";

const WINDOW_NAME = "odoo_help";
const FOLLOW_KEY = "web_context_help.follow";
const HIGHLIGHT_CLASS = "o_wch_highlight";

export const contextHelpService = {
    dependencies: ["rpc"],
    start(env, {rpc}) {
        let helpWindow = null;
        let lastContext = null;

        function isFollowing() {
            try {
                return browser.localStorage.getItem(FOLLOW_KEY) !== "0";
            } catch {
                return true;
            }
        }

        function isOpen() {
            return Boolean(helpWindow && !helpWindow.closed);
        }

        async function lookup(ctx) {
            return rpc("/web_context_help/lookup", {
                model: ctx.model,
                view_type: ctx.viewType,
                view_id: ctx.viewId,
            });
        }

        async function open(ctx) {
            lastContext = ctx;
            // Open synchronously in the click handler, or popup blockers bite
            helpWindow = browser.open("", WINDOW_NAME);
            const result = await lookup(ctx);
            if (result.url && helpWindow) {
                helpWindow.location = result.url;
                helpWindow.focus();
            }
        }

        async function notify(ctx) {
            lastContext = ctx;
            if (!isOpen() || !isFollowing()) {
                return;
            }
            const result = await lookup(ctx);
            const current = helpWindow.location.pathname + helpWindow.location.search;
            if (result.url && result.url !== current) {
                helpWindow.location = result.url;
            }
        }

        function fieldElements(field) {
            const name = CSS.escape(field);
            const selector = [
                `.o_field_widget[name="${name}"]`,
                `.o_data_cell[name="${name}"]`,
                `th[data-name="${name}"]`,
            ].join(",");
            const elements = new Set(document.querySelectorAll(selector));
            for (const widget of document.querySelectorAll(
                `.o_field_widget[name="${name}"]`
            )) {
                // Labels point to the focusable element of the widget through
                // its id, which a readonly widget does not carry: fall back to
                // the label cell of the same group row
                for (const el of [widget, ...widget.querySelectorAll("[id]")]) {
                    if (el.id) {
                        for (const label of document.querySelectorAll(
                            `label[for="${CSS.escape(el.id)}"]`
                        )) {
                            elements.add(label);
                        }
                    }
                }
                const cell = widget.closest(".o_wrap_input");
                const labelCell = cell && cell.previousElementSibling;
                if (labelCell && labelCell.classList.contains("o_wrap_label")) {
                    const label = labelCell.querySelector("label");
                    if (label) {
                        elements.add(label);
                    }
                }
            }
            return [...elements];
        }

        function highlight(field) {
            const elements = fieldElements(field).filter(
                (el) => el.offsetParent !== null
            );
            for (const el of elements) {
                el.classList.add(HIGHLIGHT_CLASS);
                browser.setTimeout(() => el.classList.remove(HIGHLIGHT_CLASS), 3000);
            }
            if (elements.length) {
                elements[0].scrollIntoView({block: "center", behavior: "smooth"});
            }
        }

        function runTour(name) {
            const tour = env.services.tour;
            if (tour && tour.run) {
                tour.run(name);
            }
        }

        browser.addEventListener("message", (ev) => {
            if (ev.origin !== browser.location.origin || !ev.data || !ev.data.type) {
                return;
            }
            if (isOpen() && ev.source !== helpWindow) {
                return;
            }
            if (!isOpen() && ev.source && ev.source.name === WINDOW_NAME) {
                // Odoo tab reloaded: take the help window back
                helpWindow = ev.source;
            }
            switch (ev.data.type) {
                case "wch_highlight":
                    highlight(ev.data.field);
                    break;
                case "wch_tour":
                    runTour(ev.data.tour);
                    break;
                case "wch_follow":
                    if (ev.data.value && lastContext) {
                        notify(lastContext);
                    }
                    break;
            }
        });

        return {open, notify, isOpen};
    },
};

registry.category("services").add("context_help", contextHelpService);
