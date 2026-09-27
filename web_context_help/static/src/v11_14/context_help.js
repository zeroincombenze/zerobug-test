/* Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
 * License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
 *
 * VERSION-DEPENDENT: Odoo 11-14 adapter (widgets, AbstractController).
 * [?] button in the control panel; opens the help window and serves its
 * postMessage requests.
 */
odoo.define("web_context_help.context_help", function (require) {
    "use strict";

    var AbstractController = require("web.AbstractController");
    var AbstractView = require("web.AbstractView");
    var ajax = require("web.ajax");
    var ControlPanel = require("web.ControlPanel");
    var core = require("web.core");

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
        var $root = controller && controller.$el ? controller.$el : $(document);
        var name = window.CSS && CSS.escape ? CSS.escape(field) : field;
        // Every field widget carries its name since Odoo 11
        var $elements = $root.find('.o_field_widget[name="' + name + '"]');
        // Labels point to the focusable element of the widget through its id,
        // which a readonly widget does not carry: fall back to the label cell
        // of the same row of the group
        var $labels = $elements.closest("tr").find("td.o_td_label label");
        $elements.add($elements.find("[id]")).each(function () {
            var id = this.getAttribute("id");
            if (id) {
                $labels = $labels.add($root.find('label[for="' + id + '"]'));
            }
        });
        $elements = $elements.add($labels);
        // List cells hold no name: find the column through its header, which
        // keeps the field name in the jQuery data, not in an attribute
        var $th = $root.find("thead th").filter(function () {
            return $(this).data("name") === field;
        });
        if ($th.length) {
            var column = $th.first().index() + 1;
            $elements = $elements
                .add($th)
                .add($root.find("tbody > tr > td:nth-child(" + column + ")"));
        }
        return $elements;
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

    AbstractView.include({
        init: function () {
            this._super.apply(this, arguments);
            // The controller gets no view id, only the fields view has it
            this.controllerParams.wchViewId = this.fieldsView.view_id;
        },
    });

    AbstractController.include({
        init: function (parent, model, renderer, params) {
            this._super.apply(this, arguments);
            this.wchViewId = params.wchViewId;
        },
        on_attach_callback: function () {
            var res = this._super.apply(this, arguments);
            // Dialogs and x2many subviews have no control panel: they keep the
            // help of the main view
            if (this.withControlPanel) {
                notify({
                    model: this.modelName,
                    viewType: this.viewType,
                    viewId: this.wchViewId,
                    controller: this,
                });
            }
            return res;
        },
    });

    return {open: open, notify: notify, isOpen: isOpen};
});
