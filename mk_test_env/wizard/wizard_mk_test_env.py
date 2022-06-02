# -*- coding: utf-8 -*-
#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import os
import re
import time
from datetime import date, datetime

import pytz
from past.builtins import basestring

from openerp import api, fields, models
from openerp.exceptions import Warning as UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ""

import python_plus
from clodoo import transodoo
from os0 import os0
from z0bug_odoo import z0bug_odoo_lib

VERSION_ERROR = 'Invalid package version! Use: pip install "%s>=%s" -U'
COMMIT_FCT = {
    "account.banking.mandate": {
        "cancel": ["back2draft"],
        "draft": ["validate"],
    },
    "account.invoice": {
        "cancel": ["action_invoice_draft"],
        "draft": ["compute_taxes", "action_invoice_open"],
    },
    "sale.order": {
        "cancel": ["action_invoice_draft"],
        "draft": ["action_confirm"],
    },
    "account.move": {
        "draft": ["_recompute_tax_lines", "post"],  # for 14.0
    },
    "stock.inventory": {
        "cancel": ["action_start"],
        "draft": ["action_validate"],
    },
}
DRAFT_FCT = {
    "account.banking.mandate": {
        "valid": ["cancel"],
        "cancel": ["back2draft"],
    },
    "account.invoice": {
        "paid": ["action_invoice_re_open"],
        "open": ["action_invoice_cancel"],
        "cancel": ["action_invoice_draft"],
        "draft": ["compute_taxes"],
    },
    "sale.order": {
        "sale": ["action_cancel"],
        "cancel": ["action__draft"],
    },
    "account.move": {
        "posted": ["button_cancel"],
    },
    "stock.inventory": {
        "cancel": ["action_start"],
    },
}

UNIQUE_REFS = ["z0bug.partner_mycompany"]
SKEYS = {
    "account.move.line": ["account_id", "credit", "debit"],
    "account.invoice": ["partner_id", "origin", "type", "date_invoice"],
    "product.supplierinfo": ["product_tmpl_id", "name"],
    "purchase.order": ["partner_id", "origin", "date_order"],
    "sale.order": ["partner_id", "client_order_ref", "date_order"],
}
ALIAS_XREF = {
    "z0bug.product_product_27": "delivery.free_delivery_carrier_product_product",
    "z0bug.product_template_27": "delivery.free_delivery_carrier_product_template",
}
T = {}
MODULES = []


@api.model
def _selection_lang(self):
    if release.version_info[0] < 10:
        return [(x.code, x.name) for x in self.env["res.lang"].search([])]
    elif release.version_info[0] < 13:
        return self.env["res.lang"].get_available()
    return [(x, y) for x, _1, y, _3, _4 in self.env["res.lang"].get_available()]


@api.model
def _selection_tz(self):
    return [
        (tz, tz)
        for tz in sorted(
            pytz.all_timezones, key=lambda tz: tz if not tz.startswith("Etc/") else "_"
        )
    ]


@api.model
def _selection_coa(self):
    if not self.COA_MODULES:
        countries = [
            "l10n_%s" % x.code.lower() for x in self.env["res.country"].search([])
        ]
        countries.insert(0, "l10n_it_nocoa")
        countries.insert(0, "l10n_it_coa")
        countries.insert(0, "l10n_it_fiscal")
        for module in self.env["ir.module.module"].search(
            [("name", "in", countries), ("state", "!=", "uninstallable")], order="name"
        ):
            if module.name.startswith("l10n_it"):
                self.COA_MODULES.insert(0, (module.name, module.shortdesc))
            else:
                self.COA_MODULES.append((module.name, module.shortdesc))
    return self.COA_MODULES


@api.model
def _selection_distro(self):
    distros = [
        ("odoo_ce", "Odoo/OCA CE"),
        ("odoo_ee", "Odoo EE/OCA"),
        ("zero", "Zeroincombenze/OCA"),
    ]
    if release.version_info[0] in (6, 12, 14):
        distros.append(("librerp", "Librerp/OCA"))
    if release.version_info[0] in (12, 14):
        distros.append(("powerp", "Powerp (deprecated)/OCA"))
    return distros


class WizardMakeTestEnvironment(models.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"
    _inherit = ["base.test.mixin"]

    STRUCT = {}
    COA_MODULES = []
    NOT_INSTALL = []
    T = {}
    _tnldict = {}

    @api.model
    def _selection_action(self, group):
        res = [("add", "Add only new records"), ("all", "Add or rewrite all records")]
        if group not in ("partner", "product", "assets"):
            res.append(("dup", "Add/duplicate all records"))
            res.append(("add-draft", "Add only new records, leave them draft"))
            res.append(("all-draft", "Set all records to draft"))
        return res

    def _test_company(self):
        recs = self.env["ir.model.data"].search(
            [("module", "=", "z0bug"), ("name", "=", "mycompany")]
        )
        if recs:
            return recs[0].res_id
        return False

    def _new_company(self):
        flag = False
        if not bool(self._test_company()):
            partner_model = self.env["res.partner"]
            domain = (
                ["|", ("customer", "!=", False), ("supplier", "!=", False)]
                if "customer" in partner_model
                else []
            )
            domain.append(
                (
                    "id",
                    "not in",
                    [x.partner_id.id for x in self.env["res.users"].search([])],
                )
            )
            domain.append(
                (
                    "id",
                    "not in",
                    [x.partner_id.id for x in self.env["res.company"].search([])],
                )
            )
            flag = bool(self.env["res.partner"].search(domain))
        return flag

    def _default_company(self):
        return self._test_company() or self.env.user.company_id.id

    @api.depends("distro")
    def _feature_2_install(self, item):
        flag = False
        if not self.module2test:
            module_list, modules_to_remove, groups_state = self.get_module_list(
                group=item)
            flag = groups_state[item]
            if flag and (
                not self.env["ir.module.module"].search(
                    [("name", "in", module_list),
                     ("state", "=", "uninstalled")]) or
                self.env["ir.module.module"].search(
                    [("name", "in", module_list),
                     ("state", "=", "uninstallable")])
            ):
                flag = False
        return flag

    def _set_coa_2_use(self):
        coa = ""
        if not self.COA_MODULES:
            _selection_coa(self)
        coa_module_list = [x[0] for x in self.COA_MODULES]
        res = self.env["ir.module.module"].search(
            [("name", "in", coa_module_list), ("state", "=", "installed")]
        )
        if res:
            coa_module_list = [x.name for x in res]
        if "l10n_it_coa" in coa_module_list:
            coa = "l10n_it_coa"
        elif "l10n_it_fiscal" in coa_module_list:
            coa = "l10n_it_fiscal"
        elif "l10n_it" in coa_module_list:
            coa = "l10n_it"
        elif coa_module_list:
            coa = coa_module_list[0]
        return coa

    @api.depends("coa")
    def _set_distro(self):
        coa = self.coa if self.coa else self._set_coa_2_use()
        if coa in ("l10n_it_coa", "l10n_it_fiscal", "l10n_it_nocoa"):
            if release.version_info[0] in (6, 12, 14):
                distro = "librerp"
            else:
                distro = "zero"
        else:
            distro = "odoo_ce"
        return distro

    def _set_lang(self):
        if self.env.user.lang and self.env.user.lang != "en_US":
            lang = self.env.user.lang
        else:
            lang = os.environ.get("LANG", "en_US").split(".")[0]
        return lang

    def _set_tz(self):
        if self.env.user.tz:
            tz = self.env.user.tz
        else:
            tz = self._context.get("tz")
            if not tz:
                try:
                    tz = os.path.join(*os.readlink("/etc/localtime").split("/")[-2:])
                except BaseException:
                    tz = "Europe/Rome"
        return tz

    state = fields.Selection(
        [
            ("", "Load modules"),
            ("1", "Load general data"),
            ("2", "Load structured data"),
            ("9", "Result"),
        ],
        readonly=True,
    )
    test_company_id = fields.Many2one(
        "res.company", string="Test Company", default=_test_company
    )
    new_company = fields.Boolean("Create new company", default=_new_company)
    company_id = fields.Many2one(
        "res.company", string="Company", required=True, default=_default_company
    )
    lang = fields.Selection(
        _selection_lang, string="Language", default=lambda self: self._set_lang()
    )
    tz = fields.Selection(
        _selection_tz, string="Timezone", default=lambda self: self._set_tz()
    )
    coa = fields.Selection(
        _selection_coa,
        "Chart of Account",
        help="Select Chart od Account to install\n"
        '"Local IT Odoo" (module l10n_it) is the minimal one\n'
        '"Powerp/Zeroincombenze" (module l10n_it_coa) is the full CoA\n'
        '"No CoA" means manual CoA\n',
        default=lambda self: self._set_coa_2_use(),
    )
    distro = fields.Selection(
        _selection_distro,
        "Odoo Ditribution/Edition",
        default=lambda self: self._set_distro(),
    )
    module2test = fields.Many2one("ir.module.module", string="Module to test")
    set_seq = fields.Boolean("Set line sequence")
    load_einvoice = fields.Boolean(
        "Activate e-Invoice", default=lambda self: self._feature_2_install(
            "load_einvoice")
    )
    load_sp = fields.Boolean(
        "Activate Split Payment",
        default=lambda self: self._feature_2_install("load_sp"),
    )
    load_rc = fields.Boolean(
        "Activate Reverse Charge",
        default=lambda self: self._feature_2_install("load_rc"),
    )
    load_wh = fields.Boolean(
        "Activate Withholding Tax",
        default=lambda self: self._feature_2_install("load_wh"),
    )
    load_li = fields.Boolean(
        "Activate Lettera di Intento",
        default=lambda self: self._feature_2_install("load_li"),
    )
    load_vat = fields.Boolean(
        "Activate VAT modules", default=lambda self: self._feature_2_install("load_vat")
    )
    load_fiscal = fields.Boolean(
        "Activate fiscal modules",
        default=lambda self: self._feature_2_install("load_fiscal"),
    )
    load_sale = fields.Selection(
        [
            ('ddt', "With module DdT"),
            ('dn', "With module Delivery Note"),
        ],
        string="Activate sale modules",
        default=lambda self: self._feature_2_install("load_sale"),
    )
    load_purchase = fields.Boolean(
        "Activate purchase module",
        default=lambda self: self._feature_2_install("load_purchase"),
    )
    load_account_plus = fields.Boolean(
        "Activate enhanced account",
        default=lambda self: self._feature_2_install("load_account_plus")
    )
    load_intrastat = fields.Boolean(
        "Activate Intrastat",
        default=lambda self: self._feature_2_install("load_intrastat")
    )
    load_conai = fields.Boolean(
        "Activate Conai", default=lambda self: self._feature_2_install("load_conai")
    )
    load_sct = fields.Boolean(
        "Activate Sepa Credit Transfer",
        default=lambda self: self._feature_2_install("load_sct"),
    )
    load_sdd = fields.Boolean(
        "Activate Sepa Direct Debit",
        default=lambda self: self._feature_2_install("load_sdd"),
    )
    load_riba = fields.Boolean(
        "Activate RiBA", default=lambda self: self._feature_2_install("load_sdd")
    )
    load_financing = fields.Boolean(
        "Activate Anticipo fatture",
        default=lambda self: self._feature_2_install("load_financing"),
    )
    load_assets = fields.Boolean(
        "Activate Assets", default=lambda self: self._feature_2_install("load_assets")
    )
    load_data_coa = fields.Selection(
        lambda self: self._selection_action("coa"), "Load Chart of Account"
    )
    load_image = fields.Boolean("Load record images", default=True)
    load_data_partner = fields.Selection(
        lambda self: self._selection_action("partner"), "Load Partners"
    )
    load_data_product = fields.Selection(
        lambda self: self._selection_action("product"), "Load Products"
    )
    load_data_sale_order = fields.Selection(
        lambda self: self._selection_action("sale"), "Load Sale Orders"
    )
    load_data_purchase_order = fields.Selection(
        lambda self: self._selection_action("purchase"), "Load Purchase Orders"
    )
    load_data_invoice = fields.Selection(
        lambda self: self._selection_action("invoice"), "Load Invoices"
    )
    load_data_assets = fields.Selection(
        lambda self: self._selection_action("assets"), "Load Assets"
    )
    ctr_rec_new = fields.Integer("New record inserted", readonly=True)
    ctr_rec_upd = fields.Integer("Record updated", readonly=True)
    ctr_rec_del = fields.Integer("Record deleted", readonly=True)
    status_mesg = fields.Text("Installation status", readonly=True)

    @api.onchange("load_sale")
    def _onchange_sale(self):
        if self.load_sale:
            pass

    @api.onchange("coa")
    def _onchange_coa(self):
        self.distro = self._set_distro()

    @api.onchange("distro")
    def _onchange_distro(self):
        if self.distro == "powerp" and release.version_info[0] not in (12, 14):
            self.distro = "zero"
        elif self.distro == "librerp" and release.version_info[0] not in (6, 12, 14):
            self.distro = "zero"

    @api.onchange(
        "module2test"
    )
    def _onchange_module2test(self):
        for item in (
            "load_einvoice",
            "load_financing",
            "load_fiscal",
            "load_sp",
            "load_rc",
            "load_wh",
            "load_li",
            "load_vat",
            "load_conai",
            "load_sct",
            "load_sdd",
            "load_riba",
            "load_financing",
            "load_assets",
            "load_sale",
            "load_purchase",
            "load_account_plus",
            "load_intrastat",
        ):
            setattr(self, item, self._feature_2_install(item))

    @api.model
    def get_value_by_coa(self, value):
        if self.distro in ("powerp", "librerp"):
            value = {
                "l10n_it": "l10n_it_coa",
            }.get(value, value)
        elif self.distro == "zero":
            value = {
                "l10n_it": "l10n_it_fiscal",
            }.get(value, value)
        elif self.distro.startswith("odoo"):
            value = {}.get(value, value)
        return value

    @api.model
    def env_ref(self, xref, retxref_id=None, company_id=None, model=None, by=None):
        """Get External Reference
        This function is like self.env.ref() with some differences:
        - If xref does not exists, return False and does not engage exception
        - Xref prefixed by 'external.' contains the key of the record
        - Some xref prefixed by 'z0bug.' are virtual with key to search for rec
        """

        def simulate_xref(xrefs, company_id, model, module=None, by=None, case=None):
            if model not in self.STRUCT:
                return False
            by = by or ("code" if "code" in self.STRUCT[model] else "name")
            if xrefs[0] == "external":
                module = None
                toks = xrefs[1].split("|")
            else:
                module = xrefs[0]
                toks = xrefs[1].split("_")[-1].split("|")
            if module:
                if (
                    self.coa == "l10n_it"
                    and module == "z0bug"
                    and model in ("account.account", "account.tax")
                ):
                    domain = [("module", "=", self.coa), ("model", "=", model)]
                else:
                    domain = [("module", "=", module), ("model", "=", model)]
                for _tok in toks[:-1]:
                    domain.append("|")
                _toks = []
                for tok in toks:
                    _toks.append(
                        "%s_%s"
                        % (
                            company_id,
                            self.translate(model, tok, ttype="value", fld_name=by),
                        )
                    )
                domain.append(("name", "in", _toks))
                recs = ir_model.search(domain)
                if len(recs) == 1:
                    if retxref_id:
                        return recs[0].id
                    return recs[0].res_id
            # xref like 'external.KEY'
            if case == "upper":
                toks = [x.upper() for x in toks]
            elif case == "lower":
                toks = [x.lower() for x in toks]
            toks = [self.translate(model, x, ttype="value", fld_name=by) for x in toks]
            if model == "account.account":
                toks = [("%s00" % x)[:6] for x in toks]
            domain = [(by, "in", toks)]
            if company_id and "company_id" in self.STRUCT[model]:
                domain.append(("company_id", "=", company_id))
            recs = self.env[model].search(domain)
            if len(recs) == 1 or (len(recs) and len(toks) > 1):
                return recs[0].id
            return False

        xrefs = self.translate("", xref, ttype="xref").split(".")
        if len(xrefs) == 2 and " " not in xref:
            ir_model = self.env["ir.model.data"]
            recs = ir_model.search([("module", "=", xrefs[0]), ("name", "=", xrefs[1])])
            if recs:
                if retxref_id:
                    return recs[0].id
                return recs[0].res_id
            elif model:
                if xrefs[0] == "external":
                    return simulate_xref(xrefs, company_id, model, by=by)
                elif model == "account.account" and xref.startswith("z0bug.coa_"):
                    return simulate_xref(xrefs, company_id, model)
                elif model == "account.tax" and xref.startswith("z0bug.tax_"):
                    return simulate_xref(xrefs, company_id, model, by="description")
                elif model == "account.journal" and xref.startswith("z0bug.jou_"):
                    return simulate_xref(xrefs, company_id, model, case="upper")
                elif model == "report.intrastat.code" and xref.startswith(
                    "z0bug.istat_"
                ):
                    return simulate_xref(xrefs, company_id, model)
                elif model == "account.fiscal.position" and xref.startswith(
                    "z0bug.fiscalpos_"
                ):
                    return simulate_xref(xrefs, company_id, model)
        return False

    @api.model
    def add_xref(self, xref, model, res_id):
        xrefs = self.translate("", xref, ttype="xref").split(".")
        if len(xrefs) != 2 or " " in xref:
            raise UserError("Invalid xref %s" % xref)
        vals = {"module": xrefs[0], "name": xrefs[1], "model": model, "res_id": res_id}
        model_model = self.env["ir.model.data"]
        xid = self.env_ref(xref, retxref_id=True)
        if not xid:
            self.ctr_rec_new += 1
            return model_model.create(vals)
        model_model.browse(xid).write(vals)
        self.ctr_rec_upd += 1
        return xid

    @api.model
    def is_to_apply(self, requirements):
        flag = True
        if requirements:
            for module in self.env["ir.module.module"].search(
                [("name", "in", requirements.split(","))]
            ):
                if module and module.state != "installed":
                    flag = False
                    break
        return flag

    @api.model
    def eval_expr(self, expr):
        """Evaluate python expression to validate current record
        Expression is a text with python expression; global variables can used.
        There are some special values:
        v (int) -> Odoo major version, i.e. 12, 14, etc.
        G (str) -> Git distro;
                   one of ('odoo_ce', 'odoo_ee', 'zero', 'powerp','librerp')
        C (str) -> Chart of Account;
                   one of ('l10n_it_[no]coa', 'l10n_it_fiscal', l10n_XX)
        xref -> Any Odoo  external reference
        """
        if not expr:
            res = True
            recalc = False
        else:
            res = False
            recalc = True
            T = {
                "v": release.version_info[0],
                "G": self.distro if self.distro else self._set_distro(),
                "C": self.coa,
            }
        max_ctr = 3
        while recalc and max_ctr:
            max_ctr -= 1
            try:
                res = eval(expr, globals(), T)
                recalc = False
            except NameError as e:
                name = str(e).split("'")[1]
                ix = expr.find(name)
                x = re.match(r"[-\w]+\.[-\w]+", expr[ix:])
                if x:
                    name = expr[ix : x.end()]
                    if len(name.split(".")) == 2:
                        m = name.replace(".", "__")
                        expr = expr.replace(name, m)
                        T[m] = os0.str2bool(self.env_ref(name), False)
                else:
                    T[name] = self.is_to_apply(name)
            except AttributeError:
                max_ctr = 0
        return res

    @api.model
    def get_module_list(self, group=None):
        def create_modules_table():
            if not MODULES:
                xmodel = "modules"
                for xref in z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(xmodel):
                    vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(xmodel, xref)
                    for item in ("modules_to_install", "modules_to_uninstall"):
                        vals[item] = (vals.get(item, "") or "").split(",")
                    vals["_requirements"] = vals.get("_requirements", "") or ""
                    MODULES.append(vals)

        def add_2_list(tgt_list, item):
            if isinstance(item, (tuple, list)):
                tgt_list += item
            else:
                tgt_list.append(item)
            return tgt_list

        create_modules_table()
        modules_2_install = []
        modules_2_remove = []
        groups_state = {}
        if group and not isinstance(group, str):
            modules_2_install = [group.name]
            for row in MODULES:
                if group in row["modules_to_install"]:
                    modules_2_remove += row["modules_to_uninstall"]
        else:
            groups = [group] if group else {x["group"] for x in MODULES}
            for item in groups:
                if item not in groups_state:
                    groups_state[item] = False
                item_val = item
                if hasattr(self, item):
                    value = getattr(self, item)
                    if value and not isinstance(value, bool):
                        item_val = '%s*%s' % (item, getattr(self, item))
                for row in MODULES:
                    if row["group"] == "*" and self.eval_expr(row["_requirements"]):
                        if not group:
                            modules_2_install += row["modules_to_install"]
                            modules_2_remove += row["modules_to_uninstall"]
                    elif (row["group"].startswith(item) and
                          self.eval_expr(row["_requirements"])):
                        if row["group"] == item_val:
                            value = True if item == item_val else item_val.split(
                                '*')[1]
                            groups_state[item] = value
                            modules_2_install += row["modules_to_install"]
                            modules_2_remove += row["modules_to_uninstall"]
                        elif (row["group"].startswith(item) and
                              "*" in row["group"] and
                              not groups_state[item]):
                            groups_state[item] = row["group"].split('*')[1]
                            modules_2_install += row["modules_to_install"]
                            modules_2_remove += row["modules_to_uninstall"]
            if not group:
                coa_module_list = [x[0] for x in self.COA_MODULES]
                if not any([x for x in modules_2_install if x in coa_module_list]):
                    modules_2_install.append(self.get_value_by_coa("l10n_it"))
        module_list = []
        for module in modules_2_install:
            distro_module = self.translate("ir.module.module", module, ttype="merge")
            if distro_module and distro_module != module:
                module_list = add_2_list(module_list, module)
                module_list = add_2_list(module_list, distro_module)
            else:
                distro_module = self.translate("", module, ttype="module")
                if (
                    isinstance(distro_module, (tuple, list))
                    and module not in distro_module
                ) or distro_module != module:
                    if distro_module:
                        module_list = add_2_list(module_list, distro_module)
                    modules_2_remove.append(module)
                else:
                    module_list = add_2_list(module_list, module)
        modules_2_install = module_list
        return list(set(modules_2_install)), list(set(modules_2_remove)), groups_state

    @api.model
    def install_modules(
        self, modules_to_install, modules_to_remove, no_clear_cache=None
    ):
        flag_module_installed = False
        modules_model = self.env["ir.module.module"]
        to_install_modules = modules_model
        modules_found = []
        modules_2_test = []
        coa_module_list = [x[0] for x in self.COA_MODULES]
        for module in modules_model.search([("name", "in", modules_to_install)]):
            if not module:
                # Module does not exist in current Odoo version
                continue
            elif module.state == "to install":
                if module.name not in self.NOT_INSTALL:
                    self.NOT_INSTALL.append(module.name)
                    self.install_modules([module.name], [], no_clear_cache=True)
                modules_found.append(module.name)
                modules_2_test.append(module.name)
                continue
            elif module.state == "uninstalled":
                if len(modules_to_install) != 1 and module.name in coa_module_list:
                    # CoA modules must be installed before others
                    self.install_modules([module.name], [], no_clear_cache=True)
                    modules_found.append(module.name)
                    modules_2_test.append(module.name)
                    flag_module_installed = True
                    continue
                to_install_modules += module
                self.status_mesg += 'Module "%s" installed\n' % module.name
                modules_found.append(module.name)
                modules_2_test.append(module.name)
                self.ctr_rec_new += 1
            elif module.state == "uninstallable":
                self.status_mesg += 'Module "%s" cannot be installed!\n' % module.name
                modules_found.append(module.name)
            elif module.state == "installed":
                self.status_mesg += 'Module "%s" was already installed\n' % module.name
                modules_found.append(module.name)
        for module in list(set(modules_to_install) - set(modules_found)):
            if module:
                self.status_mesg += 'Module "%s" not found in this database!\n' % module
        for module in self.NOT_INSTALL:
            self.status_mesg += (
                'Module "%s" may be inconsistent;'
                " please try to install manually!\n" % module
            )
        max_time_to_wait = 2

        modules_to_remove = list(set(modules_to_remove) - set(modules_to_install))
        if modules_to_remove:
            to_remove_modules = modules_model
            for module in modules_model.search(
                [("name", "in", modules_to_remove), ("state", "=", "installed")]
            ):
                to_remove_modules += module
                self.status_mesg += 'Module "%s" uninstalled\n' % module.name
                self.ctr_rec_upd += 1
                flag_module_installed = True
            to_remove_modules.module_uninstall()
            max_time_to_wait += len(to_remove_modules)
            while max_time_to_wait > 0:
                time.sleep(1)
                max_time_to_wait -= 1
                if not modules_model.search(
                    [("name", "in", modules_to_remove), ("state", "=", "installed")]
                ):
                    break

        if to_install_modules:
            to_install_modules.button_immediate_install()
            max_time_to_wait += len(to_install_modules)
        found_uninstalled = True
        while max_time_to_wait > 0 and found_uninstalled:
            time.sleep(1)
            max_time_to_wait -= 1
            found_uninstalled = False
            for module in modules_model.search(
                [("name", "in", modules_2_test), ("state", "!=", "installed")]
            ):
                found_uninstalled = module
                break
        if found_uninstalled and not isinstance(found_uninstalled, bool):
            raise UserError("Module %s not installed!" % found_uninstalled.name)

        if (not to_install_modules and modules_to_remove) or (
            to_install_modules and not modules_to_remove
        ):
            time.sleep(2)
        else:
            time.sleep(1)
        if not no_clear_cache and to_install_modules and modules_to_remove:
            # We need to invalidate cache to load model of installed modules
            if release.version_info[0] < 12:
                self.env.invalidate_all()
        return flag_module_installed

    def get_tnldict(self):
        if not self._tnldict:
            transodoo.read_stored_dict(self._tnldict)
        return self._tnldict

    def get_tgtver(self):
        distro = self.distro if self.distro else self._set_distro()
        return self.get_distro_version(distro)

    def translate(self, model, src, ttype=None, fld_name=False):
        tgtver = self.get_tgtver()
        srcver = "librerp12"
        if release.major_version == srcver:
            if ttype == "valuetnl":
                return ""
            return src
        if ttype == "xref":
            src = ALIAS_XREF.get(src, src)
        return transodoo.translate_from_to(
            self.get_tnldict(),
            model,
            src,
            srcver,
            tgtver,
            ttype=ttype,
            fld_name=fld_name,
        )

    def setup_model_structure(self, model):
        """Store model structure into memory"""
        if not model:
            return
        if model in self.STRUCT:
            return
        if model in self.env:
            self.STRUCT[model] = self.env[model].fields_get()
        else:
            raise UserError("Model %s not found!" % model)

    def bind_record(
        self,
        model,
        vals,
        company_id,
        field=None,
        parent_id=None,
        parent_name=None,
        retrec=None,
        params=None,
    ):
        params = params or {}
        domain = []
        multi_key = parent_id and parent_name in self.STRUCT[model]
        if model == "account.payment.term.line" or (
            self.set_seq and multi_key and "sequence" in self.STRUCT[model]
        ):
            fields = ("sequence",)
        elif model in SKEYS:
            fields = SKEYS[model]
            multi_key = True
        else:
            fields = (
                "code",
                "code_prefix",
                "acc_number",
                "login",
                "description",
                "depreciation_type_id",
                "name",
                "number",
                "partner_id",
                "product_id",
                "product_tmpl_id",
                "sequence",
                "tax_src_id",
                "tax_dest_id",
            )
        for nm in fields:
            if nm == parent_name:
                continue
            elif nm == "code" and model == "product.product":
                continue
            elif nm == "description" and model != "account.tax":
                continue
            elif nm == "sequence" and not multi_key:
                continue
            if nm in vals and nm in self.STRUCT[model]:
                if (
                    isinstance(vals[field or nm], basestring)
                    and "%(" in vals[field or nm]
                ):
                    domain.append((nm, "=", vals[field or nm] % params))
                else:
                    domain.append((nm, "=", vals[field or nm]))
                if not multi_key:
                    break
        if domain:
            if parent_id and parent_name in self.STRUCT[model]:
                domain.append((parent_name, "=", parent_id))
            if "company_id" in self.STRUCT[model]:
                domain.append(("company_id", "=", company_id))
            recs = self.env[model].with_context({"lang": "en_US"}).search(domain)
            if not recs and model == "product.product":
                del domain[-1]
                recs = self.env[model].with_context({"lang": "en_US"}).search(domain)
            if len(recs) == 1:
                return recs[0] if retrec else recs[0].id
        return False

    @api.model
    def map_fields(
        self,
        model,
        vals,
        company_id,
        parent_id=None,
        parent_model=None,
        mode=None,
        only_fields=[],  # pylint: disable=dangerous-default-value
        ref_model=None,
    ):
        def expand_many(item):
            try:
                item = [x for x in item.split(",")]
            except BaseException:
                pass
            return item

        def cast_type(field, attrs, vals):
            if attrs["type"] == "boolean":
                vals[field] = os0.str2bool(vals[field], False)
            elif attrs["type"] in ("float", "monetary") and isinstance(
                vals[field], basestring
            ):
                vals[field] = eval(vals[field])
            elif attrs["type"] in ("date", "datetime"):
                vals[field] = python_plus.compute_date(vals[field])
                if (
                    field == "date"
                    and vals[field]
                    and isinstance(vals[field], basestring)
                ):
                    params["year"] = vals[field][:4]
            elif (
                attrs["type"] in ("many2one", "one2many", "many2many", "integer")
                and isinstance(vals[field], basestring)
                and (
                    vals[field].isdigit()
                    or vals[field].startswith("-")
                    and vals[field][1:].isdigit()
                )
            ):
                vals[field] = int(vals[field])
            return vals

        self.setup_model_structure(model)
        ref_model = ref_model or model
        ref_image = self.translate(ref_model, "image", ttype="field")
        if self.load_image and vals.get("id") and ref_image in self.STRUCT[model]:
            filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(vals["id"])
            if filename:
                vals[ref_image] = z0bug_odoo_lib.Z0bugOdoo().get_image(vals["id"])
        if mode == "dup":
            del vals["id"]
        params = {
            "year": str(date.today().year)
            if date.today().month > 1
            else str(date.today().year - 1)
        }
        if (
            model == "account.invoice"
            and release.major_version >= 13
            and vals.get("price_unit", 0.0) < 0.0 <= vals.get("quantity", 0.0)
        ) or (
            model == "sale_order"
            and release.major_version >= 13
            and vals.get("price_unit", 0.0) < 0.0 <= vals.get("product_uom_qty", 0.0)
        ):
            vals["price_unit"] = -vals.get("price_unit", 0.0)
            vals["product_uom_qty"] = -vals.get("product_uom_qty", 0.0)
        # Translate field name from Odoo 12.0
        for field in vals.copy().keys():
            name = self.translate(ref_model, field, ttype="field")
            if name != field:
                vals[name] = vals[field]
                del vals[field]
            self.setup_model_structure(self.STRUCT[model].get(name, {}).get("relation"))
        parent_name = ""
        multi_model = parent_id and parent_name
        for field in vals.copy().keys():
            if (
                (only_fields and field != "id" and field not in only_fields)
                or vals[field] is None
                or vals[field] in ("None", r"\N")
            ):
                del vals[field]
                continue
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                del vals[field]
                mesg = 'Model "%s" w/o field "%s"!!!\n' % (model, field)
                if mesg not in self.status_mesg:
                    self.status_mesg += mesg
                continue
            vals = cast_type(field, attrs, vals)
            if self.translate(ref_model, vals[field], ttype="valuetnl", fld_name=field):
                vals[field] = self.translate(
                    ref_model, vals[field], ttype="value", fld_name=field
                )
            if field == "id":
                if multi_model:
                    del vals[field]
                elif isinstance(vals[field], basestring):
                    vals[field] = self.env_ref(
                        vals[field], company_id=company_id, model=model
                    )
                    if not vals[field]:
                        del vals[field]
            elif parent_id and (
                (parent_model and attrs.get("relation", "/") == parent_model)
                or (not parent_model and attrs.get("relation", "/") == model)
            ):
                vals[field] = parent_id
                parent_name = field
                multi_model = True
            elif field == "company_id":
                vals[field] = company_id
                continue
            elif (
                field == "reconcile"
                and model == "account.account"
                and release.version_info[0] >= 14
            ):
                del vals[field]
            elif attrs["type"] in ("many2one", "one2many", "many2many"):
                if isinstance(vals[field], basestring):
                    if attrs["type"] == "many2one":
                        items = [vals[field]]
                    else:
                        items = expand_many(vals[field])
                    res = []
                    for item in items:
                        if len(item.split(".")) == 2 and " " not in item:
                            try:
                                xid = self.env_ref(
                                    item % params,
                                    company_id=company_id,
                                    model=attrs["relation"],
                                )
                            except ValueError:
                                raise UserError("Invalid xref %s" % item)
                            if xid:
                                res.append(xid)
                        elif isinstance(item, basestring) and item.isdigit():
                            res.append(eval(item))
                        elif item:
                            self.setup_model_structure(attrs["relation"])
                            item = self.bind_record(
                                model, item, company_id, field=field, params=params
                            )
                            if item:
                                res.append(item)
                    if len(res):
                        if attrs["type"] == "many2one":
                            vals[field] = res[0]
                        else:
                            vals[field] = [(6, 0, res)]
                    else:
                        del vals[field]
                continue
            elif attrs.get("relation"):
                self.setup_model_structure(attrs["relation"])
                value = self.bind_record(
                    model, vals, company_id, field=field, params=params
                )
                if value:
                    vals[field] = value
                else:
                    del vals[field]
        if model == "account.account":
            if "user_type_id" in vals:
                if self.STRUCT[model].get("nature", {}):
                    if isinstance(vals["user_type_id"], int):
                        acc = self.env["account.account.type"].browse(
                            vals["user_type_id"]
                        )
                    else:
                        acc = self.env["account.account.type"].browse(
                            self.env_ref(vals["user_type_id"])
                        )
                    if acc.nature:
                        vals["nature"] = acc.nature
        if (
            model == "res.partner"
            and vals.get("parent_id")
            and release.version_info[0] > 10
            and not vals.get("name")
        ):
            vals["name"] = (
                "%s (Spedizione)" % self.env[model].browse(vals["parent_id"]).name
            )
        if multi_model:
            if mode != "dup":
                rec = self.bind_record(
                    model,
                    vals,
                    company_id,
                    parent_id=parent_id,
                    parent_name=parent_name,
                    retrec=True,
                    params=params,
                )
                if rec:
                    vals["id"] = rec.id
                elif "id" in vals:
                    del vals["id"]
        return vals, parent_name

    def browse_xid(self, model, xid):
        rec = None
        if model == "res.company" and xid == -1:
            rec = self.company_id
        elif model in ("res.groups", "res.users") and xid == -1:
            rec = self.env.user
        elif model and xid:
            rec = self.env[model].browse(xid)
        return rec

    def drop_unchanged_fields(self, vals, model, xid):
        rec = self.browse_xid(model, xid)
        for field in vals.copy():
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                del vals[field]
            if isinstance(vals[field], basestring) and vals[field]:
                if attrs["type"] in ("float", "integer"):
                    vals[field] = eval(vals[field])
            if rec and not rec[field] and not vals[field]:
                del vals[field]
                continue
            if rec and rec[field] and vals[field]:
                if attrs["type"] == "many2one":
                    if vals[field] == rec[field].id:
                        del vals[field]
                elif attrs["type"] in ("one2many", "many2many"):
                    if rec[field]:
                        value = [(6, 0, [x.id for x in rec[field]])]
                        if value == vals[field]:
                            del vals[field]
                elif attrs["type"] == "boolean":
                    if isinstance(vals[field], bool) and vals[field] == rec[field]:
                        del vals[field]
                    elif os0.str2bool(vals[field], False) == rec[field]:
                        del vals[field]
                elif isinstance(vals[field], float) and round(vals[field], 3) == round(
                    rec[field], 3
                ):
                    del vals[field]
                elif (
                    isinstance(vals[field], (basestring, int, date, datetime))
                    and vals[field] == rec[field]
                ):
                    del vals[field]
        return vals

    @api.model
    def write_diff(self, model, xid, vals, xref, parent_id=None, parent_model=None):
        vals = self.drop_unchanged_fields(vals, model, xid)
        if "id" in vals:
            del vals["id"]
        multi_model = parent_id and parent_model
        if vals:
            if multi_model:
                if parent_model in DRAFT_FCT:
                    self.do_draft(parent_model, parent_id)
            elif model in DRAFT_FCT:
                self.do_draft(model, xid)
            try:
                if model.startswith("account.move"):
                    self.browse_xid(model, xid).with_context(
                        check_move_validity=False
                    ).write(vals)
                else:
                    self.browse_xid(model, xid).write(vals)
                self.ctr_rec_upd += 1
                if not parent_model and not parent_id:
                    mesg = '- Xref "%s":"%s" updated\n' % (model, xref)
                    self.status_mesg += mesg
            except BaseException as e:
                self._cr.rollback()  # pylint: disable=invalid-commit
                self.status_mesg += "*** Record %s: error %s!!!\n" % (xref, e)

    @api.model
    def create_new(self, model, xid, vals, xref, parent_id=None, parent_model=None):
        for name in ("id", "valid_for_dichiarazione_intento"):
            if name in vals:
                del vals[name]
        if "code" in self.STRUCT[model] and "code" not in vals:
            vals["code"] = vals.get("name")
        try:
            if model.startswith("account.move"):
                xid = (
                    self.env[model]
                    .with_context(check_move_validity=False)
                    .create(vals)
                    .id
                )
            else:
                xid = self.env[model].create(vals).id
            self.ctr_rec_new += 1
            if not parent_model and not parent_id:
                mesg = '- Xref "%s":"%s" added\n' % (model, xref)
                self.status_mesg += mesg
        except BaseException as e:
            self._cr.rollback()  # pylint: disable=invalid-commit
            self.status_mesg += "*** Record %s: error %s!!!\n" % (xref, e)
            xid = False
        return xid

    @api.model
    def store_rec_with_xref(
        self,
        xref,
        model,
        company_id,
        ref_model=None,
        parent_id=None,
        parent_model=None,
        seq=None,
        mode=None,
        only_fields=[],
    ):  # pylint: disable=dangerous-default-value
        """Store record into DB
        Args:
            xref (str): external reference (format 'module.key')
            model (str): odoo model name
            company_id (m2o): company id
            parent_id (m2o): parent record id (id current record is child)
            parent_model (str): parent record odoo model name
            seq (int): sequence number (if model has sequence field)
            mode (str): action behavior; value are:
                'add' -> add only new records
                'add-draft' -> add only new records but keep them draft
                'all' -> write all records
                'all-draft' -> write all records but keep them draft
                'dup' -> duplicate record
            only_fields (list): list fo field to manage (empty means all)

        Returns:
            record id
        """
        ref_model = ref_model or model
        if mode == "dup" and xref in UNIQUE_REFS:
            mode = "all"
        if parent_id and parent_model and parent_model != "product.template":
            xid = False
        else:
            xid = self.env_ref(xref, company_id=company_id, model=model)
        if not xid or mode in ("all", "all2", "all-draft", "dup"):
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(ref_model, xref)
            if "_requirements" in vals:
                if not self.eval_expr(vals["_requirements"]):
                    return False
                del vals["_requirements"]
            if "sequence" in self.STRUCT[model] and seq and not vals.get("sequence"):
                vals["sequence"] = seq
            vals, parent_name = self.map_fields(
                model,
                vals,
                company_id,
                parent_id=parent_id,
                parent_model=parent_model,
                mode=mode,
                only_fields=only_fields,
                ref_model=ref_model,
            )
            if not vals or list(vals.keys()) == ["id"]:
                return xid
            if mode == "dup":
                xid = False
            else:
                if vals.get("id") and isinstance(vals["id"], int):
                    xid = vals["id"]
                if not xid:
                    xid = self.bind_record(
                        model,
                        vals,
                        company_id,
                        parent_id=parent_id,
                        parent_name=parent_name,
                    )
            if only_fields and not xid:
                return xid
            if xid:
                if not mode.startswith("add"):
                    self.write_diff(
                        model,
                        xid,
                        vals,
                        xref,
                        parent_id=parent_id,
                        parent_model=parent_model,
                    )
            else:
                xid = self.create_new(
                    model, xid, vals, xref, parent_id=None, parent_model=None
                )
            if (
                xid
                and parent_model == "product.template"
                or (not parent_id and not parent_model)
            ):
                self.add_xref(xref, model, xid)
        return xid

    @api.model
    def do_workflow(self, model, rec_id, FCT, ignore_error=None):
        def do_action(model, action):
            action = self.translate(model, action, ttype="action")
            if action and hasattr(self.env[model], action):
                if action in ("compute_taxes", "_recompute_tax_lines"):
                    if release.version_info[0] < 13:
                        # Please, do not remove this write: set default values
                        saved_date = rec.date
                        rec.write({"date": False})
                        rec.write({"date": saved_date})
                try:
                    getattr(rec, action)()
                    if (
                        hasattr(rec, "intrastat")
                        and rec.intrastat
                        and action
                        in (
                            "compute_taxes",
                            "_recompute_tax_lines",
                        )
                    ):
                        # Compute intrastat lines
                        rec.compute_intrastat_lines()
                except BaseException as e:
                    if not ignore_error:
                        raise UserError(
                            "Action %s.%s FAILED (%s)!" % (model, action, e)
                        )

        self._cr.commit()  # pylint: disable=invalid-commit
        if model in FCT:
            stated = []
            rec = self.env[model].browse(rec_id)
            while rec.state in FCT[model]:
                old_state = rec.state
                if old_state in stated:
                    break
                stated.append(old_state)
                for action in FCT[model][old_state]:
                    do_action(model, action)
                rec = self.env[model].browse(rec_id)

    @api.model
    def do_draft(self, model, rec_id):
        self.do_workflow(model, rec_id, DRAFT_FCT)

    @api.model
    def do_commit(self, model, rec_id, mode=None):
        if model == "account.fiscal.position":
            if (
                rec_id == self.env_ref("z0bug.fiscalpos_li")
                and "valid_for_dichiarazione_intento" in self.STRUCT[model]
            ):
                self.env[model].browse(rec_id).write(
                    {"valid_for_dichiarazione_intento": True}
                )
        if not mode or not mode.endswith("-draft"):
            self.do_workflow(model, rec_id, COMMIT_FCT, ignore_error=True)

    @api.model
    def set_bank_acc(self):
        model = "account.account"
        if self.coa in ("l10n_it_coa", "l10n_it_fiscal") and model in self.env:
            prefix = self.company_id.bank_account_code_prefix
            if prefix:
                self.setup_model_structure(model)
                acc_model = self.env[model]
                for rec in acc_model.search([("code", "like", "%s%%" % prefix)]):
                    if not rec.code.startswith(prefix):
                        continue
                    vals = {}
                    if not rec.group_id:
                        vals["group_id"] = self.env_ref(
                            "external.%s" % prefix,
                            model="account.group",
                            by="code_prefix",
                        )
                    if hasattr(rec, "nature") and not rec.nature:
                        vals["nature"] = "P"
                    if vals:
                        rec.write(vals)

    @api.model
    def write_spec_rec(self, model, vals):
        if (
            model in ("res.groups", "res.users")
            and "groups_id" in vals
            and not vals["groups_id"]
        ):
            del vals["groups_id"]
        if model == "res.users" and not vals:
            vals = {
                "lang": self.lang,
                "tz": self.tz,
                "company_id": self.env_ref("z0bug.mycompany"),
            }
        if not vals:
            return
        vals, parent_name = self.map_fields(model, vals, self.company_id.id)
        vals = self.drop_unchanged_fields(vals, model, -1)
        if vals:
            self.browse_xid(model, -1).write(vals)
            self.ctr_rec_upd += 1
            self.status_mesg += '- Xref "%s":"%s" updated\n' % (model, vals.keys())

    @api.model
    def make_misc(self):
        def setup_group(key, value, cur_value):
            v = os0.str2bool(value, None)
            if v is not None:
                value = v
            res = cur_value or []
            name = self.translate("", key, ttype="xref")
            gid = False
            if len(name.split(".")) == 2 and " " not in name:
                gid = self.env_ref(name)
                if isinstance(gid, bool):
                    modules = self.env["ir.module.module"].search(
                        [('name', '=', key.split('.')[0])])
                    if not modules or modules[0].state == "installed":
                        self.ctr_rec_upd += 1
                        self.status_mesg += ('- Xref "%s": Unknown!\n' % key)
                    return res
            if isinstance(value, bool):
                if value and gid not in self.env.user.groups_id.ids:
                    res.append((4, gid))
                    self.status_mesg += "Group %s enabled\n" % name
                elif not value and gid in self.env.user.groups_id.ids:
                    res.append((3, gid))
                    self.status_mesg += "Group %s disabled\n" % name
            return res

        def split_field(value):
            values = value.split(".")
            return ".".join(values[0:-1]), values[-1]

        self.set_bank_acc()
        for model in ("res.company", "res.groups", "res.users"):
            self.setup_model_structure(model)
        xmodel = "miscellaneous"
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(xmodel)
        prior_model = ""
        vals = {}
        for xref in sorted(xrefs):
            xvals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(xmodel, xref)
            model, field = split_field(xvals["id"])
            if not xvals.get("key"):
                key = None
            else:
                key = xvals["key"]
                field = None
            if not self.eval_expr(xvals["_requirements"]):
                continue
            del xvals["_requirements"]
            if model != prior_model:
                if prior_model and vals:
                    self.write_spec_rec(prior_model, vals)
                prior_model = model
                vals = {}
            if model == "res.company":
                if field in self.STRUCT[model]:
                    vals[field] = xvals["value"]
            elif model in ("res.groups", "res.users"):
                vals["groups_id"] = setup_group(
                    key, xvals["value"], vals.get("groups_id")
                )
        if prior_model and vals:
            self.write_spec_rec(prior_model, vals)

    @api.model
    def make_model(
        self,
        model,
        mode=None,
        model2=None,
        cantdup=None,
        only_fields=[],  # pylint: disable=dangerous-default-value
        only_xrefs=[],
    ):  # pylint: disable=dangerous-default-value
        def store_1_rec(xref, seq, parent_id, deline_list):
            if only_xrefs and xref not in only_xrefs:
                return False, seq, deline_list
            if model2:
                model2_model = self.env[model2]
            if model2 and xref not in hdr_list:
                # Found child xref, evaluate parent xref
                if model2 == "product.product":
                    parent_id = self.env_ref(xref.replace("_product", "_template"))
                else:
                    parent_id = self.env_ref("_".join(xref.split("_")[0:-1]))
                if parent_id:
                    if model == "account.payment.term":
                        seq += 1
                    elif self.set_seq:
                        seq += 10
                    else:
                        seq = 10
                    rec_line_id = self.store_rec_with_xref(
                        xref,
                        model2 or model,
                        company_id,
                        ref_model=ref_model2,
                        mode=mode,
                        parent_id=parent_id,
                        parent_model=model,
                        seq=seq,
                        only_fields=only_fields,
                    )
                    if rec_line_id in deline_list:
                        del deline_list[deline_list.index(rec_line_id)]
            else:
                if seq:
                    # Previous write was a detail record
                    if deline_list:
                        if model.startswith("account.move"):
                            model2_model.browse(deline_list).with_context(
                                check_move_validity=False
                            ).unlink()
                        else:
                            model2_model.browse(deline_list).unlink()
                    self.do_commit(model, parent_id, mode=mode)
                deline_list = []
                parent_id = self.store_rec_with_xref(
                    xref,
                    model,
                    company_id,
                    ref_model=ref_model,
                    mode=mode,
                    only_fields=only_fields,
                )
                if not parent_id and not model2 and not not seq and model in COMMIT_FCT:
                    self.do_commit(model, parent_id, mode=mode)
                if parent_id and model2:
                    if "sequence" in self.STRUCT[model2]:
                        seq = 1 if model == "account.payment.term" else 10
                        for rec_line in model2_model.search(
                            [(parent_name, "=", parent_id)], order="sequence,id"
                        ):
                            if model.startswith("account.move"):
                                rec_line.with_context(check_move_validity=False).write(
                                    {"sequence": seq}
                                )
                            else:
                                rec_line.write({"sequence": seq})
                            if model == "account.payment.term":
                                seq += 1
                            elif self.set_seq:
                                seq += 10
                            else:
                                seq = 10
                            deline_list.append(rec_line.id)
                    else:
                        model2_model.search([(parent_name, "=", parent_id)]).unlink()
                seq = 0
            return parent_id, seq, deline_list

        # V14.0 has different model for invoices
        ref_model = model
        model = self.translate("", model, ttype="model")
        if cantdup and mode == "dup":
            mode = "all"
        mode = mode or "all"
        if model not in self.env:
            self.status_mesg += '- Model "%s" not found!\n' % model
            return
        self.setup_model_structure(model)
        company_id = False
        if "company_id" in self.STRUCT[model]:
            company_id = self.company_id.id
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(ref_model)
        if not xrefs:
            raise UserError("No test record found for model %s!" % model)
        if None in xrefs:
            raise UserError("Detected a NULL record in test data for model %s!" % model)
        hdr_list = [x for x in xrefs]
        deline_list = []
        parent_id = False
        parent_name = ""
        xrefs2 = []
        if model2:
            ref_model2 = model2
            model2 = self.translate("", model2, ttype="model")
            if model2 not in self.env:
                self.status_mesg += '- Model "%s" not found!\n' % model2
                return
            self.setup_model_structure(model2)
            for name, field in self.STRUCT[model2].items():
                if field.get("relation") == model:
                    parent_name = name
                    break
            xrefs2 = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(ref_model2)
        if model == "account.account":
            xrefs_list = []
            for xref in sorted(xrefs):
                # Prima i mastri
                if len(xref) == 12:
                    xrefs_list.append(xref)
            for xref in sorted(xrefs):
                # poi i capoconti
                if len(xref) == 13:
                    xrefs_list.append(xref)
            for xref in sorted(xrefs):
                # infine i sottoconti
                if 12 < len(xref) > 13:
                    xrefs_list.append(xref)
        elif model == "product.template":
            xrefs_list = sorted(xrefs)
            for xref in xrefs2:
                xref_parent = xref.replace("_product", "_template")
                xrefs_list.insert(xrefs_list.index(xref_parent) + 1, xref)
        elif xrefs2:
            xrefs_list = sorted(xrefs + xrefs2)
            del xrefs2
        else:
            xrefs_list = sorted(xrefs)

        if None in xrefs:
            raise UserError(
                "Detected a NULL record in test data for model %s!" % model2
            )

        seq = 0
        for xref in xrefs_list:
            parent_id, seq, deline_list = store_1_rec(xref, seq, parent_id, deline_list)
        if seq:
            if deline_list:
                self.env[model2].browse(deline_list).unlink()
            self.do_commit(model, parent_id, mode=mode)
        elif not parent_id and not model2 and not not seq and model in COMMIT_FCT:
            self.do_commit(model, parent_id, mode=mode)
        self._cr.commit()  # pylint: disable=invalid-commit

    @api.model
    def make_model_limited(self, model, mode=None, model2=None, cantdup=None):
        def make_model_limited_partner(self):
            return [], [
                "z0bug.partner_mycompany",
                "z0bug.partner_mycompany_uk",
                "z0bug.partner_mycompany_de",
                "z0bug.partner_mycompany_fr",
            ]

        def make_model_limited_tax(self):
            model = "account.tax"
            if not self._feature_2_install("load_rc"):
                for name in ("kind_id", "rc_type", "rc_sale_tax_id"):
                    name = self.translate(model, name, ttype="field")
                    only_fields.append(name)
            if not self._feature_2_install("load_sp"):
                for name in ("payability",):
                    name = self.translate(model, name, ttype="field")
                    only_fields.append(name)
            return only_fields, []

        def make_model_limited_account(self):
            return [], [
                "z0bug.coa_180003",
                "z0bug.coa_180004",
                "z0bug.coa_180005",
                "z0bug.coa_180006",
                "z0bug.coa_180007",
            ]

        only_fields = []
        only_xrefs = []
        if model == "res.partner":
            only_fields, only_xrefs = make_model_limited_partner(self)
        elif model == "account.tax":
            only_fields, only_xrefs = make_model_limited_tax(self)
        elif model == "account.account":
            only_fields, only_xrefs = make_model_limited_account(self)
        if only_fields or only_xrefs:
            return self.make_model(
                model,
                mode=mode,
                model2=model2,
                cantdup=cantdup,
                only_fields=only_fields,
                only_xrefs=only_xrefs,
            )

    @api.model
    def set_company_to_test(self, company):
        self.add_xref("z0bug.mycompany", "res.company", company.id)
        self.add_xref("z0bug.partner_mycompany", "res.partner", company.partner_id.id)

    @api.model
    def set_user_preference(self):
        self.write_spec_rec("res.users", {})

    @api.model
    def enable_cancel_journal(self):
        model = "account.journal"
        if (
            not self._feature_2_install("load_vat")
            and "update_posted" in self.STRUCT[model]
        ):
            journal_model = self.env[model]
            for rec in journal_model.search([("update_posted", "=", False)]):
                rec.write({"update_posted": True})

    @api.model
    def load_language(self, iso=None):
        iso = iso or "en_US"
        lang_model = self.env["res.lang"]
        languages = lang_model.search([("code", "=", iso)])
        if not languages:
            languages = lang_model.search([("code", "=", iso), ("active", "=", False)])
            if languages:
                languages.write({"active": True})
        if not languages:
            vals = {"lang": iso, "overwrite": False}
            try:
                self.env["base.language.install"].create(vals).lang_install()
                self.status_mesg += 'Language "%s" installed\n' % iso
            except BaseException:
                self.status_mesg += 'Cannot install language "%s"!!!\n' % iso
        if iso != "en_US":
            vals = {"lang": iso}
            try:
                self.env["base.update.translations"].create(vals).act_update()
                self.status_mesg += 'Update translation "%s"\n' % iso
            except BaseException:
                self.status_mesg += 'Cannot translate "%s"!!!\n' % iso

    def diff_ver(self, min_version, module, comp):
        text_module_ver = "0"
        for ver_name in ("__version__", "version"):
            if hasattr(globals()[comp], ver_name):
                text_module_ver = ".".join(
                    [
                        "%03d" % int(x)
                        for x in getattr(globals()[comp], ver_name).split(".")
                    ]
                )
                break
        text_min_ver = ".".join(["%03d" % int(x) for x in min_version.split(".")])
        if text_module_ver < text_min_ver:
            raise UserError(VERSION_ERROR % (module, min_version))

    def make_test_environment(self, cr, uid, ids, context=None):
        wizard = self
        self = wizard.browse(cr, uid, ids[0], context=context)
        self.cr = cr
        self.uid = uid
        self.env = self.pool

        self.diff_ver("1.0.14", "z0bug_odoo", "z0bug_odoo_lib")
        self.diff_ver("1.0.4", "clodoo", "transodoo")
        self.diff_ver("1.0.3", "os0", "os0")
        self.diff_ver("1.0.10", "python_plus", "python_plus")

        # Block 0: TODO> Separate function
        self.ctr_rec_new = 0
        self.ctr_rec_upd = 0
        self.ctr_rec_del = 0
        self.status_mesg = 'Target distro/version "%s"\n' % self.get_tgtver()
        self.load_language()
        if self.lang and self.lang != self.env.user.lang:
            self.load_language(iso=self.lang)
        if self.new_company:
            self.make_model_limited("res.partner", cantdup=True)
            self.make_model("res.company", cantdup=True)
            self.company_id = self.env_ref("z0bug.mycompany")
            if self.company_id not in [x for x in self.env.user.company_ids]:
                self.env.user.write({"company_ids": [(4, self.company_id.id)]})
        elif not self.test_company_id:
            self.set_company_to_test(self.company_id)
            self.make_model_limited("res.partner", cantdup=True)
            self.make_model("res.company", cantdup=True)
        self.set_user_preference()
        self._cr.commit()  # pylint: disable=invalid-commit
        modules_to_install, modules_to_remove, groups_state = self.get_module_list(
            group=self.module2test)
        flag_module_installed = self.install_modules(
            modules_to_install, modules_to_remove
        )
        if flag_module_installed:
            return {
                "name": "Data created",
                "type": "ir.actions.act_window",
                "res_model": "wizard.make.test.environment",
                "view_type": "form",
                "view_mode": "form",
                "res_id": self.id,
                "target": "new",
                "context": {"active_id": self.id},
                "view_id": self.env.ref("mk_test_env.result_mk_test_env_view").id,
                "domain": [("id", "=", self.id)],
            }
        self.state = "1"
        self.make_misc()

        # Block 1: TODO> Separate function
        if self.load_data_coa:
            if self.coa == "l10n_it_no_coa":
                self.make_model("account.account",
                                mode=self.load_data_coa, cantdup=True)
                self.make_model("account.tax", mode=self.load_data_coa, cantdup=True)
            self.make_model_limited("account.account",
                                    mode=self.load_data_coa, cantdup=True)
            self.make_model_limited("account.tax",
                                    mode=self.load_data_coa, cantdup=True)
            self.make_model("decimal.precision", mode=self.load_data_coa, cantdup=True)
            if release.version_info[0] == 10 and not self._feature_2_install("load_rc"):
                self.make_model(
                    "account_rc_type",
                    mode=self.load_data_coa, model2="account_rc_type.tax"
                )
            self.make_model(
                "account.fiscal.position",
                mode=self.load_data_coa,
                model2="account.fiscal.position.tax",
            )
            self.make_model("italy.profile.account", mode=self.load_data_coa)
            self.make_model("date.range.type", mode=self.load_data_coa, cantdup=True)
            self.make_model("date.range", mode=self.load_data_coa, cantdup=True)
            self.make_model("account.fiscal.year", mode=self.load_data_coa)
            self.make_model(
                "account.payment.term",
                mode=self.load_data_coa,
                model2="account.payment.term.line",
            )
            self.make_model("account.journal", mode=self.load_data_coa, cantdup=True)
            self.make_model("res.bank", mode=self.load_data_coa, cantdup=True)
        if self.load_fiscal:
            self.enable_cancel_journal()
        if self.load_data_coa and not self._feature_2_install("load_wh"):
            self.make_model(
                "withholding.tax",
                mode=self.load_data_coa,
                model2="withholding.tax.rate",
                cantdup=True,
            )
        if self.load_data_partner:
            self.make_model("res.partner", mode=self.load_data_partner)
            self.make_model(
                "res.partner.bank", mode=self.load_data_partner, cantdup=True)
            if not self._feature_2_install("load_sdd"):
                self.make_model(
                    "account.banking.mandate", mode=self.load_data_partner, cantdup=True
                )
        if self.load_data_product:
            self.make_model(
                "product.template",
                mode=self.load_data_product,
                cantdup=True,
                model2="product.product",
            )
        if self.load_data_partner and self.load_data_product:
            self.make_model(
                "product.supplierinfo", mode=self.load_data_product, cantdup=True
            )
        if self.load_data_partner or self.load_data_coa:
            if self.env_ref("z0bug.res_partner_1") and self.env_ref("z0bug.jou_ncc"):
                # Reload to link bank account to journal
                self.make_model(
                    "account.journal",
                    mode=self.load_data_coa or self.load_data_partner,
                    cantdup=True,
                )
                self.make_model(
                    "account.payment.mode",
                    mode=self.load_data_coa or self.load_data_partner,
                    cantdup=True,
                )
            if self.env_ref("z0bug.res_partner_6") and not self._feature_2_install(
                "load_li"
            ):
                self.make_model(
                    "dichiarazione.intento.yearly.limit",
                    mode=self.load_data_coa,
                    cantdup=True,
                )
                self.make_model(
                    "dichiarazione.intento", mode=self.load_data_coa, cantdup=True
                )
        if self.load_data_assets and not self._feature_2_install("load_assets"):
            self.make_model(
                "asset.category",
                mode=self.load_data_assets,
                cantdup=True,
                model2="asset.category.depreciation.type",
            )
            self.make_model("asset.asset", mode=self.load_data_assets, cantdup=True)
        self.make_misc()
        self.state = "2"

        # Block 2: TODO> Separate function
        if self.load_data_sale_order or self.load_data_purchase_order:
            self.make_model(
                "stock.inventory",
                mode=self.load_data_sale_order,
                model2="stock.inventory.line",
            )
        if self.load_data_sale_order:
            self.make_model(
                "sale.order", mode=self.load_data_sale_order, model2="sale.order.line"
            )
        if self.load_data_purchase_order:
            self.make_model(
                "purchase.order",
                mode=self.load_data_purchase_order,
                model2="purchase.order.line",
            )
        if self.load_data_invoice:
            self.make_model(
                "account.invoice",
                mode=self.load_data_invoice, model2="account.invoice.line"
            )
            self.make_model(
                "account.move", mode=self.load_data_invoice, model2="account.move.line"
            )
        self.status_mesg += "Data (re)loaded.\n"
        self.state = "9"
        self.make_misc()

        return {
            "name": "Data created",
            "type": "ir.actions.act_window",
            "res_model": "wizard.make.test.environment",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"active_id": self.id},
            "view_id": self.env.ref("mk_test_env.result_mk_test_env_view").id,
            "domain": [("id", "=", self.id)],
        }

    def close_window(self):
        return {"type": "ir.actions.act_window_close"}
