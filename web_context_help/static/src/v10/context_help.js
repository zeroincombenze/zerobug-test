/* Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
 * License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
 *
 * VERSION-DEPENDENT: Odoo 10 adapter (widgets, ViewManager).
 * [?] button in the control panel; opens the help window and serves its
 * postMessage requests.
 */
odoo.define("web_context_help.context_help", function (require) {
    "use strict";

    var ajax = require("web.ajax");
    var ControlPanel = require("web.ControlPanel");
    var core = require("web.core");
    var ViewManager = require("web.ViewManager");

    var WINDOW_NAME = "odoo_help";
    var FOLLOW_KEY = "web_context_help.follow";
    var HIGHLIGHT_CLASS = "o_wch_highlight";

    var helpWindow = null;
    // Active view of the main action: {model, viewType, viewId, controller}
    var lastContext = null;

    function isFollowing() {
        try {
            return window.localStorage.getItem(FOLLOW_KEY) !== "0";
        } catch (e) {
            return true;
        }
    }

    function isOpen() {
        return Boolean(helpWindow && !helpWindow.closed);
    }

    function lookup(ctx) {
        return ajax.jsonRpc("/web_context_help/lookup", "call", {
            model: ctx.model,
            view_type: ctx.viewType,
            view_id: ctx.viewId,
        });
    }

    function open(ctx) {
        // Open synchronously in the click handler, or popup blockers bite
        helpWindow = window.open("", WINDOW_NAME);
        if (!ctx) {
            return;
        }
        lookup(ctx).then(function (result) {
            if (result.url && helpWindow) {
                helpWindow.location = result.url;
                helpWindow.focus();
            }
        });
    }

    function notify(ctx) {
        lastContext = ctx;
        if (!isOpen() || !isFollowing()) {
            return;
        }
        lookup(ctx).then(function (result) {
            var current = helpWindow.location.pathname + helpWindow.location.search;
            if (result.url && result.url !== current) {
                helpWindow.location = result.url;
            }
        });
    }

    function fieldElements(field) {
        var controller = lastContext && lastContext.controller;
        var $elements = $();
        // Form view: widgets carry no name, ask the view
        var widget = controller && controller.fields && controller.fields[field];
        if (widget && widget.$el) {
            $elements = $elements.add(widget.$el);
            if (widget.$label) {
                $elements = $elements.add(widget.$label);
            }
        }
        var name = window.CSS && CSS.escape ? CSS.escape(field) : field;
        var $root = controller && controller.$el ? controller.$el : $(document);
        return $elements.add(
            $root.find('td[data-field="' + name + '"], th[data-id="' + name + '"]')
        );
    }

    function highlight(field) {
        var $elements = fieldElements(field).filter(":visible");
        $elements.addClass(HIGHLIGHT_CLASS);
        setTimeout(function () {
            $elements.removeClass(HIGHLIGHT_CLASS);
        }, 3000);
        if ($elements.length) {
            $elements[0].scrollIntoView({block: "center", behavior: "smooth"});
        }
    }

    function runTour(name) {
        // web_tour is optional: not a dependency of this module
        var services = odoo.__DEBUG__ && odoo.__DEBUG__.services;
        var tour = services && services["web_tour.tour"];
        if (tour && tour.run) {
            tour.run(name);
        }
    }

    window.addEventListener("message", function (ev) {
        if (ev.origin !== window.location.origin || !ev.data || !ev.data.type) {
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

    ControlPanel.include({
        start: function () {
            // Before _super: it detaches the contents while the panel is hidden.
            // The x2many control panel has no o_cp_right
            this.$(".o_cp_right").append(
                $(core.qweb.render("web_context_help.Button")).on("click", function () {
                    open(lastContext);
                })
            );
            return this._super.apply(this, arguments);
        },
    });

    ViewManager.include({
        _display_view: function () {
            var self = this;
            return this._super.apply(this, arguments).done(function () {
                // Dialogs (headless) keep the help of the main view
                if (self.flags.headless || !self.active_view) {
                    return;
                }
                var controller = self.active_view.controller;
                var fields_view = (controller && controller.fields_view) || {};
                notify({
                    model: self.dataset && self.dataset.model,
                    viewType: self.active_view.type,
                    viewId: fields_view.view_id,
                    controller: controller,
                });
            });
        },
    });

    return {open: open, notify: notify, isOpen: isOpen};
});
