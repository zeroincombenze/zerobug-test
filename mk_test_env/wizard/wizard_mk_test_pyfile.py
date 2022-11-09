#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# import time
# import re
# import pytz
import itertools
import os
from datetime import datetime

from past.builtins import basestring

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import odoo.release as release
    except ImportError:
        release = ""

import python_plus
from clodoo import transodoo
from os0 import os0
from z0bug_odoo import z0bug_odoo_lib

VERSION_ERROR = "Invalid package version! Use: pip install '%s>=%s' -U"
SOURCE_HEADER = """\"\"\"
Tests are based on test environment created by module mk_test_env in repository
https://github.com/zeroincombenze/zerobug-test

Each model is declared by a dictionary which name should be "TEST_model",
where model is the uppercase model name with dot replaced by "_".
i.e.: res_partner -> TEST_RES_PARTNER

Every record is declared in the model dictionary by a key which is the external
reference used to retrieve the record.
i.e. the following record is named 'z0bug.partner1':
TEST_RES_PARTNER = {
    "z0bug.partner1": {
        "name": "Alpha",
        "street": "1, First Avenue",
        ...
    }
}

The magic dictionary TEST_SETUP contains data to load at test setup.
TEST_SETUP = {
    "res.partner": TEST_RES_PARTNER,
    ...
}

In setup() function, the following code
    self.setup_records(lang="it_IT")
creates all record declared by above data; lang is an optional parameter.

Final notes:
* Many2one value must be declared as external identifier
* Written on %s by mk_test_env %s
\"\"\"
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)

"""
SYSTEM_MODEL_ROOT = [
    "base.config.",
    "base_import.",
    "base.language.",
    "base.module.",
    "base.setup.",
    "base.update.",
    "ir.actions.",
    "ir.exports.",
    "ir.model.",
    "ir.module.",
    "ir.qweb.",
    "report.",
    "res.config.",
    "web_editor.",
    "web_tour.",
    "workflow.",
]
SYSTEM_MODELS = [
    "_unknown",
    "base",
    "base.config.settings",
    "base_import",
    "change.password.wizard",
    "ir.autovacuum",
    "ir.config_parameter",
    "ir.exports",
    "ir.fields.converter",
    "ir.filters",
    "ir.http",
    "ir.logging",
    "ir.model",
    "ir.needaction_mixin",
    "ir.qweb",
    "ir.rule",
    "ir.translation",
    "ir.ui.menu",
    "ir.ui.view",
    "ir.values",
    "mail.alias",
    "mail.followers",
    "mail.message",
    "mail.notification",
    "report",
    "res.config",
    "res.font",
    "res.groups",
    "res.request.link",
    "res.users.log",
    "web_tour",
    "workflow",
]
TABLE_DEF = {
    "account.account": {
        "user_type_id": {"required": True},
    },
    "account.invoice": {
        "number": {"required": False},
    },
    "purchase.order": {
        "name": {"required": False},
    },
    "sale.order": {
        "name": {"required": False},
    },
    "stock.picking.package.preparation": {
        "ddt_number": {"required": False},
    },
}
SOURCE_BODY = """
TNL_RECORDS = {
    "product.product": {
        # "type": ["product", "consu"],
    },
    "product.template": {
        # "type": ["product", "consu"],
    },
}


class %(model_class)s(common.TransactionCase):

    # --------------------------------------- #
    # Common code: may be share among modules #
    # --------------------------------------- #

    def simulate_xref(self, xref, raise_if_not_found=None,
                      model=None, by=None, company=None, case=None):
        \"\"\"Simulate External Reference
        This function simulates self.env.ref() searching for model record.
        Ordinary xref is formatted as "MODULE.NAME"; when MODULE = "external"
        this function is called.
        Record is searched by <by> parameter, default is "code" or "name";
        id NAME is formatted as "FIELD=VALUE", FIELD value is assigned to <by>
        If company is supplied, it is added in search domain;

        Args:
            xref (str): external reference
            raise_if_not_found (bool): raise exception if xref not found or
                                       if more records found
            model (str): external reference model
            by (str): default field to search object record,
            company (obj): default company
            case: apply for uppercase or lowercase

        Returns:
            obj: the model record
        \"\"\"
        if model not in self.env:
            if raise_if_not_found:
                raise ValueError("Model %%s not found in the system" %% model)
            return False
        _fields = self.env[model].fields_get()
        if not by:
            if model in self.by:
                by = self.by[model]
            else:
                by = "code" if "code" in _fields else "name"
        module, name = xref.split(".", 1)
        if "=" in name:
            by, name = name.split("=", 1)
        if case == "upper":
            name = name.upper()
        elif case == "lower":
            name = name.lower()
        domain = [(by, "=", name)]
        if (model not in ("product.product",
                          "product.template",
                          "res.partner",
                          "res.users") and
                company and "company_id" in _fields):
            domain.append(("company_id", "=", company.id))
        objs = self.env[model].search(domain)
        if len(objs) == 1:
            return objs[0]
        if raise_if_not_found:
            raise ValueError("External ID not found in the system: %%s" %% xref)
        return False

    def env_ref(self, xref, raise_if_not_found=None,
                model=None, by=None, company=None, case=None):
        \"\"\"Get External Reference
        This function is like self.env.ref(); if xref does not exist and
        xref prefix is "external.", engage simulate_xref

        Args:
            xref (str): external reference, format is "module.name"
            raise_if_not_found (bool): raise exception if xref not found
            model (str): external ref. model; required for "external." prefix
            by (str): field to search for object record (def "code" or "name")
            company (obj): default company

        Returns:
            obj: the model record
        \"\"\"
        if xref is False or xref is None:
            return xref
        obj = self.env.ref(xref, raise_if_not_found=raise_if_not_found)
        if not obj:
            module, name = xref.split(".", 1)
            if module == "external":
                return self.simulate_xref(xref,
                                          model=model,
                                          by=by,
                                          company=company,
                                          case=case)
        return obj

    def add_xref(self, xref, model, xid):
        \"\"\"Add external reference that will be used in next tests.
        If xref exist, result ID will be upgraded\"\"\"
        module, name = xref.split(".", 1)
        if module == "external":
            return False
        ir_model = self.env["ir.model.data"]
        vals = {
            "module": module,
            "name": name,
            "model": model,
            "res_id": xid,
        }
        xrefs = ir_model.search([("module", "=", module),
                                 ("name", "=", name)])
        if not xrefs:
            return ir_model.create(vals)
        xrefs[0].write(vals)
        return xrefs[0]

    def get_values(self, model, values, by=None, company=None, case=None):
        \"\"\"Load data values and set them in a dictionary for create function
        * Not existent fields are ignored
        * Many2one field are filled with current record ID
        \"\"\"
        _fields = self.env[model].fields_get()
        vals = {}
        if model in TNL_RECORDS:
            for item in TNL_RECORDS[model].keys():
                if item in values:
                    (old, new) = TNL_RECORDS[model][item]
                    if values[item] == old:
                        values[item] = new
        for item in values.keys():
            if item not in _fields:
                continue
            if item == "company_id" and not values[item]:
                vals[item] = company.id
            elif _fields[item]["type"] == "many2one":
                res = self.env_ref(
                    values[item],
                    model=_fields[item]["relation"],
                    by=by,
                    company=company,
                    case=case,
                )
                if res:
                    vals[item] = res.id
            elif (_fields[item]["type"] == "many2many" and
                  "." in values[item] and
                  " " not in values[item]):
                res = self.env_ref(
                    values[item],
                    model=_fields[item]["relation"],
                    by=by,
                    company=company,
                    case=case,
                )
                if res:
                    vals[item] = [(6, 0, [res.id])]
            elif values[item] is not None:
                vals[item] = values[item]
        return vals

    def model_create(self, model, values, xref=None):
        \"\"\"Create a test record and set external ID to next tests\"\"\"
        if model.startswith("account.move"):
            res = self.env[model].with_context(
                check_move_validity=False).create(values)
        else:
            res = self.env[model].create(values)
        if xref and " " not in xref:
            self.add_xref(xref, model, res.id)
        return res

    def model_browse(self, model, xid, company=None, by=None,
                     raise_if_not_found=True):
        \"\"\"Browse a record by external ID\"\"\"
        res = self.env_ref(
            xid,
            model=model,
            company=company,
            by=by,
        )
        if res:
            return res
        return self.env[model]

    def model_make(self, model, values, xref, company=None, by=None):
        \"\"\"Create or write a test record and set external ID to next tests\"\"\"
        res = self.model_browse(model,
                                xref,
                                company=company,
                                by=by,
                                raise_if_not_found=False)
        if res:
            if model.startswith("account.move"):
                res.with_context(check_move_validity=False).write(values)
            else:
                res.write(values)
            return res
        return self.model_create(model, values, xref=xref)

    def default_company(self):
        return self.env.user.company_id

    def set_locale(self, locale_name, raise_if_not_found=True):
        modules_model = self.env["ir.module.module"]
        modules = modules_model.search([("name", "=", locale_name)])
        if modules and modules[0].state != "uninstalled":
            modules = []
        if modules:
            modules.button_immediate_install()
            self.env["account.chart.template"].try_loading_for_current_company(
                locale_name
            )
        else:
            if raise_if_not_found:
                raise ValueError(
                    "Module %%s not found in the system" %% locale_name)

    def install_language(self, iso, overwrite=None, force_translation=None):
        iso = iso or "en_US"
        overwrite = overwrite or False
        load = False
        lang_model = self.env["res.lang"]
        languages = lang_model.search([("code", "=", iso)])
        if not languages:
            languages = lang_model.search([("code", "=", iso),
                                           ("active", "=", False)])
            if languages:
                languages.write({"active": True})
                load = True
        if not languages or load:
            vals = {
                "lang": iso,
                "overwrite": overwrite,
            }
            self.env["base.language.install"].create(vals).lang_install()
        if force_translation:
            vals = {"lang": iso}
            self.env["base.update.translations"].create(vals).act_update()

    def setup_records(
        self, lang=None, locale=None, company=None, save_as_demo=None
    ):
        \"\"\"Create all record from declared data. See above doc

        Args:
            lang (str): install & load specific language
            locale (str): install locale module with CoA; i.e l10n_it
            company (obj): declare default company for tests
            save_as_demo (bool): commit all test data as they are demo data
            Warning: usa save_as_demo carefully; is used in multiple tests,
            like in travis this option can be cause to failue of tests
            This option can be used in local tests with "run_odoo_debug -T"

        Returns:
            None
        \"\"\"

        def iter_data(model, model_data, company):
            for item in model_data.keys():
                if isinstance(model_data[item], str):
                    continue
                vals = self.get_values(
                    model,
                    model_data[item],
                    company=company)
                res = self.model_make(
                    model, vals, item,
                    company=company)
                if model == "product.template":
                    model2 = "product.product"
                    vals = self.get_values(
                        model2,
                        model_data[item],
                        company=company)
                    vals["product_tmpl_id"] = res.id
                    self.model_make(
                        model2, vals, item.replace("template", "product"),
                        company=company)

        self.save_as_demo = save_as_demo or False
        if locale:
            self.set_locale(locale)
        if lang:
            self.install_language(lang)
        if not self.env["ir.module.module"].search(
                [("name", "=", "stock"), ("state", "=", "installed")]):
            TNL_RECORDS["product.product"]["type"] = ["product", "consu"]
            TNL_RECORDS["product.template"]["type"] = ["product", "consu"]
        company = company or self.default_company()
        self.by = {}
        for model, model_data in TEST_SETUP.items():
            by = model_data.get("by")
            if by:
                self.by[model] = by
        for model in TEST_SETUP_LIST:
            model_data = TEST_SETUP[model]
            iter_data(model, model_data, company)

    # ------------------ #
    # Specific test code #
    # ------------------ #
    def setUp(self):
        super(%(super_args)s).setUp()
        self.setup_records(%(opt_lang)s)

    def tearDown(self):
        super(%(super_args)s).tearDown()
        if self.save_as_demo:
            self.env.cr.commit()               # pylint: disable=invalid-commit

    def %(test_fct_name)s(self):
        # Here an example of code you should insert to test
        # Example is based on account.invoice
        model = "%(model)s"
        model_child = "%(model_child)s"
        for xref in %(title)s:
            _logger.info(
                "🎺 Testing %%s[%%s]" %% (model, xref)
            )
            vals = self.get_values(
                model,
                %(title)s[xref])
            res = self.model_make(model, vals, xref)

            for xref_child in %(title_child)s.values():
                if xref_child["%(parent_id_name)s"] == xref:
                    vals = self.get_values(model_child, xref_child)
                    vals["%(parent_id_name)s"] = res.id
                    self.model_make(model_child, vals, False)
            # res.compute_taxes()

            self.assertEqual(
                "left", "right",
                msg="Left value is different from right value")
"""


@api.model
def _selection_lang(self):
    if release.version_info[0] < 13:
        return self.env["res.lang"].get_available()
    return [(x, y) for x, y, _2, _3, _4 in self.env["res.lang"].get_available()]


class WizardMkTestPyfile(models.TransientModel):
    _name = "wizard.mk.test.pyfile"
    _description = "Create python source test file"
    _inherit = ["base.test.mixin"]

    def _default_model2ignore(self):
        return [
            x.id
            for x in self.env["ir.model"].search(
                [
                    (
                        "model",
                        "in",
                        [
                            "asset.category",
                            "account.asset",
                            "account.group",
                            "fatturapa.payment_method",
                            "fatturapa.payment_term",
                            "italy.conai.partner.category",
                            "italy.conai.product.category",
                            "mail.activity",
                            "product.category",
                            "res.currency",
                            "stock.location",
                            "stock.location.route",
                            "stock.warehouse",
                            "report.intrastat.code",
                        ],
                    )
                ]
            )
        ]

    def _set_lang(self):
        if self.env.user.lang and self.env.user.lang != "en_US":
            lang = self.env.user.lang
        else:
            lang = os.environ.get("LANG", "en_US").split(".")[0]
            if not self.env["res.lang"].search([("code", "=", lang)]):
                lang = "en_US"
        return lang

    module2test = fields.Many2one("ir.module.module", string="Module to test")
    lang = fields.Selection(
        _selection_lang, string="Language", default=lambda self: self._set_lang()
    )
    xref_ids = fields.Many2many("ir.model.data", string="External references")
    oca_coding = fields.Boolean("OCA coding", default=True)
    product_variant = fields.Boolean("Add product variant", default=False)
    max_child_records = fields.Integer("Max child records", default=2)
    # model4install_ids = fields.Many2many(
    #     comodel_name="ir.model",
    #     relation="ir_model_4_install_rel",
    #     string="Models by installed modules",
    #     default=_default_model2ignore)
    model2ignore_ids = fields.Many2many(
        comodel_name="ir.model",
        relation="ir_model_2_ignore_rel",
        string="Models to ignore",
        default=_default_model2ignore,
    )
    source = fields.Text("Source code")

    # modules2install = fields.Many2many(
    #     "ir.module.module",
    #     string="Modules to install")
    _tnldict = {}
    _model2ignore = []

    OCA_TNL = {
        "external.FAT|FATT|INV": "external.INV",
        "external.ACQ|FATTU|BILL": "external.BILL",
        "z0bug.tax_a15v": "external.00art15v",
        "z0bug.tax_a15a": "external.00art15a",
        "z0bug.tax_10v": "external.10v",
        "z0bug.tax_10a": "external.10a",
        "z0bug.tax_22v": "external.22v",
        "z0bug.tax_22a": "external.22a",
        "z0bug.tax_4v": "external.4v",
        "z0bug.tax_4a": "external.4a",
        "z0bug.tax_5v": "external.5v",
        "z0bug.tax_5a": "external.5a",
        "z0bug.partner_mycompany": "base.main_partner",
    }
    MODEL_BY = {
        "account.tax": "description",
        "product.template": "default_code",
        "product.product": "default_code",
    }
    HIDDEN_FIELDS = {
        "account.account": ["group_id"],
        "account.fiscal.position": ["sequence"],
        "account.journal": ["sequence", "group_inv_lines_mode"],
        "account.tax": ["sequence"],
        "product.template": ["categ_id", "intrastat_type", "route_ids"],
        "product.product": ["categ_id", "intrastat_type", "route_ids"],
    }

    @api.onchange("module2test")
    def onchange_module2test(self):
        _model4install = []
        xref_ids = set()
        if self.module2test:
            modules = self.get_dependency_names(self.module2test)
            for model in self.env["ir.model"].search([]):
                modules4model = {x.strip() for x in model.modules.split(",")}
                if modules4model & set(modules):
                    if model not in _model4install:
                        _model4install.append(model)
                        if (
                            xref_ids
                            or self.module2test.name not in modules4model
                            or model.model
                            not in (
                                "sale.order",
                                "purchase.order",
                                "account.invoice",
                                "account.move",
                            )
                        ):
                            continue
                        xref_ids = set(
                            self.env["ir.model.data"].search(
                                [
                                    ("module", "in", (self.module2test.name, "z0bug")),
                                    ("model", "=", model.model),
                                    ("name", "like", "1"),
                                ]
                            )
                        )
            self.xref_ids = [(6, 0, [x.id for x in xref_ids])]

    def model_to_manage(self, model, exclude=None):
        return (
            model not in SYSTEM_MODEL_ROOT
            and model not in SYSTEM_MODELS
            and model not in (exclude or [])
        )

    def get_tnldict(self):
        if not self._tnldict:
            transodoo.read_stored_dict(self._tnldict)
        return self._tnldict

    def get_tgtver(self):
        return self.get_distro_version("odoo" if self.oca_coding else "librerp")

    def translate(self, model, src, ttype=False, fld_name=False):
        tgtver = self.get_tgtver()
        srcver = "librerp12"
        if srcver == tgtver:
            if ttype == "valuetnl":
                return ""
            return src
        return transodoo.translate_from_to(
            self.get_tnldict(),
            model,
            src,
            srcver,
            tgtver,
            ttype=ttype,
            fld_name=fld_name,
        )

    def get_xref_obj(self, xref):
        ir_model = self.env["ir.model.data"]
        module, name = xref.split(".", 1)
        xrefs = ir_model.search([("module", "=", module), ("name", "=", name)])
        if not xrefs:
            return False
        return xrefs[0]

    def get_model_class(self, model):
        items = model.split(".")
        model_class = ""
        for item in items:
            model_class += item[0].upper() + item[1:]
        return model_class

    def get_child_model(self, model):
        model_line = "%s.line" % model
        if model_line not in self.env:
            model_line = "%s.rate" % model
            if model_line not in self.env:
                model_line = False
        return model_line

    def push_xref(self, xref, model, top=None):
        self.model_of_xref[xref] = model
        module, name = xref.split(".", 1)
        if module not in self.modules_to_declare:
            return
        vals = self.get_test_values(model, xref)
        if not vals:
            return
        if xref not in self.sound_xrefs:
            self.sound_xrefs.append(xref)
        if model not in self.sound_models:
            self.sound_models.append(model)
        if model not in self.struct:
            self.struct[model] = self.env[model].fields_get()
        for field in vals.keys():
            if (
                field == "id"
                or field not in self.struct[model]
                or vals[field] is None
                or vals[field] in ("None", r"\N")
            ):
                continue
            if self.struct[model][field].get("relation"):
                relation = self.struct[model][field]["relation"]
                if relation in TABLE_DEF and "required" in TABLE_DEF[relation]:
                    required = TABLE_DEF[relation]["required"]
                else:
                    required = top or False
                if not required:
                    model_ids = self.env["ir.model"].search([("model", "=", relation)])
                    if model_ids[0] in self.model2ignore_ids:
                        self.model2ignore_ids = [(3, model_ids[0].id)]
                    continue
                if vals[field] not in self.dep_xrefs:
                    self.dep_xrefs.append(vals[field])
                    model_child = self.get_child_model(
                        self.struct[model][field]["relation"]
                    )
                    if not model_child:
                        self.push_xref(
                            vals[field], self.struct[model][field]["relation"]
                        )
                    else:
                        self.push_child_xref(
                            vals[field],
                            self.struct[model][field]["relation"],
                            model_child,
                        )

    def push_child_xref(self, xref, model, model_child, top=None):
        if model not in self.struct:
            self.struct[model] = self.env[model].fields_get()
        if model_child not in self.struct:
            self.struct[model_child] = self.env[model_child].fields_get()
        if xref not in self.top_child_xrefs:
            self.top_child_xrefs[xref] = []
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model_child)
        record_ctr = 0
        parent_id_name = ""
        for xref_child in xrefs:
            if self.max_child_records and record_ctr >= self.max_child_records:
                break
            self.model_of_xref[xref_child] = model_child
            vals = self.get_test_values(model_child, xref_child)
            for field in vals.keys():
                if (
                    field == "id"
                    or field not in self.struct[model_child]
                    or vals[field] is None
                    or vals[field] in ("None", r"\N")
                ):
                    continue
                if (
                    self.struct[model_child][field]["type"] == "many2one"
                    and self.struct[model_child][field].get("relation")
                    and self.struct[model_child][field]["relation"] == model
                ):
                    if vals[field] == xref:
                        self.top_child_xrefs[xref].append(xref_child)
                        parent_id_name = field
                        record_ctr += 1
                    break
        for xref_child in self.top_child_xrefs[xref]:
            self.push_xref(xref_child, model_child)
        return parent_id_name

    def get_context_xref(self, xref, model, fld_name=None):
        oca_xref = self.translate("", xref, ttype="xref")
        if fld_name:
            oca_xref = self.translate(model, oca_xref, ttype="value", fld_name=fld_name)
        if oca_xref == xref:
            if model == "account.account":
                module, xid = xref.split(".", 1)
                if module == "external":
                    xid = self.translate(model, xid, ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
                elif module == "z0bug" and xid.startswith("coa_"):
                    xid = self.translate(model, xid[4:], ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
            elif model == "account.tax":
                module, xid = xref.split(".", 1)
                if module == "external":
                    xid = self.translate(model, xid, ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
                elif module == "z0bug" and xid.startswith("tax_"):
                    xid = self.translate(model, xid[4:], ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
            elif model == "report.intrastat.code":
                module, xid = xref.split(".", 1)
                if module == "external":
                    xid = self.translate(model, xid, ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
                elif module == "z0bug" and xid.startswith("istat_"):
                    xid = self.translate(model, xid[6:], ttype="value", fld_name="code")
                    oca_xref = "external.%s" % xid
        if self.oca_coding:
            oca_xref = self.OCA_TNL.get(xref, oca_xref)
        return oca_xref

    def write_source_model(self, model, xrefs, exclude_xref=None):
        def cast_type(field, attrs, vals):
            if attrs["type"] == "boolean":
                vals[field] = os0.str2bool(vals[field], False)
            elif attrs["type"] in ("float", "monetary") and isinstance(
                vals[field], basestring
            ):
                vals[field] = eval(vals[field])
            elif attrs["type"] in ("date", "datetime"):
                vals[field] = python_plus.compute_date(vals[field])
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

        if not self.product_variant and model == "product.product":
            return "", False, ""
        exclude_xref = exclude_xref or []
        xrefs = xrefs or self.sound_xrefs
        valid = False
        title = "TEST_%s" % model.replace(".", "_").upper()
        source = "%s = {\n" % title
        if model in self.MODEL_BY:
            source += "    \"by\": \"%s\",\n" % self.MODEL_BY[model]
        toc = ""
        for xref in xrefs:
            if xref in exclude_xref or self.model_of_xref[xref] != model:
                continue
            oca_xref = self.get_context_xref(xref, self.model_of_xref[xref])
            source += "    \"%s\": {\n" % oca_xref
            valid = True
            toc = "    \"%s\": %s,\n" % (model, title)
            vals = self.get_test_values(model, xref)
            if model in self.HIDDEN_FIELDS:
                for field in self.HIDDEN_FIELDS[model]:
                    if field in vals:
                        del vals[field]
            if oca_xref != xref:
                module, oca_name = oca_xref.split(".", 1)
                if model == "account.account":
                    vals["code"] = oca_name
                elif model == "account.tax":
                    vals["description"] = oca_name
                elif model == "account.journal":
                    vals["code"] = oca_name
            for field in vals.keys():
                if (
                    field == "id"
                    or field not in self.struct[model]
                    or vals[field] is None
                    or vals[field] in ("None", r"\N")
                ):
                    continue
                if field == "lang" and not self.lang:
                    continue
                if field == "currency_id":
                    continue
                vals = cast_type(field, self.struct[model][field], vals)
                if self.struct[model][field]["type"] in (
                    "many2one",
                    "one2many",
                    "many2many",
                ) and isinstance(vals[field], basestring):
                    if self.struct[model][field]["relation"] in self._model2ignore:
                        continue
                    vals[field] = self.get_context_xref(
                        vals[field],
                        self.struct[model][field]["relation"],
                        fld_name=field,
                    )
                if self.struct[model][field]["type"] in (
                    "integer",
                    "float",
                    "monetary",
                ):
                    source += "        \"%s\": %s,\n" % (field, vals[field])
                elif self.struct[model][field]["type"] == "boolean":
                    source += "        \"%s\": %s,\n" % (
                        field,
                        "True" if vals[field] else "False",
                    )
                else:
                    source += "        \"%s\": \"%s\",\n" % (field, vals[field])
            source += "    },\n"
        source += "}\n"
        return source, valid, toc

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

    def make_test_pyfile(self):
        self.diff_ver("2.0.0", "z0bug_odoo", "z0bug_odoo_lib")
        self.diff_ver("2.0.0", "clodoo", "transodoo")
        self.diff_ver("2.0.0", "os0", "os0")
        self.diff_ver("2.0.0", "python_plus", "python_plus")
        self.modules_to_declare = ("z0bug", "external", "l10n_it")
        self.model_of_xref = {}
        self.top_xrefs = []
        self.top_model_xrefs = {}
        self.top_child_xrefs = {}
        self.sound_xrefs = []
        self.sound_models = []
        self.struct = {}
        self.dep_xrefs = []
        self._model2ignore = [x.model for x in self.model2ignore_ids]

        # Phase 1:
        # find & store all xrefs child or depending on required xrefs
        parent_id_name = ""
        for xref_obj in self.xref_ids:
            xref = "%s.%s" % (xref_obj.module, xref_obj.name)
            if xref in self.top_xrefs:
                continue
            self.top_xrefs.append(xref)
            model = xref_obj.model
            if model not in self.top_model_xrefs:
                self.top_model_xrefs[model] = []
            if xref not in self.top_model_xrefs[model]:
                self.top_model_xrefs[model].append(xref)
            model_child = self.get_child_model(model)
            if model_child:
                parent_id_name = self.push_child_xref(
                    xref, model, model_child, top=True
                )
            self.push_xref(xref, model, top=True)

        # Phase 2:
        # For every model depending on required model, write field data
        self.source = ""
        if release.version_info[0] < 11:
            self.source = "# -*- coding: utf-8 -*-\n"
        self.source += SOURCE_HEADER % (
            datetime.today(),
            self.env["ir.module.module"]
            .search([("name", "=", "mk_test_env")])
            .latest_version,
        )
        self.source += "# Record data for base models\n"
        test_setup_list = "TEST_SETUP_LIST = [\n"
        test_setup = "TEST_SETUP = {\n"
        for model in sorted(self.sound_models):
            source, valid, toc = self.write_source_model(
                model,
                self.sound_xrefs,
                exclude_xref=self.top_xrefs
                + list(itertools.chain(*self.top_child_xrefs.values())),
            )
            if valid:
                self.source += source
                test_setup_list += "    \"%s\",\n" % model
                test_setup += toc
        test_setup_list += "]\n"
        test_setup += "}\n"
        self.source += test_setup_list
        self.source += test_setup

        # Phase 3:
        # For every model child of required model, write field data
        self.source += "\n# Record data for child models\n"
        for model in sorted(self.top_model_xrefs.keys()):
            model_child = self.get_child_model(model)
            if not model_child:
                continue
            child_xrefs = []
            for xref in self.top_model_xrefs[model]:
                if xref in self.top_child_xrefs:
                    child_xrefs += self.top_child_xrefs[xref]
            source, valid, toc = self.write_source_model(model_child, child_xrefs)
            if valid:
                self.source += source

        # Phase 4:
        # Finally write required model field data
        self.source += "\n# Record data for models to test\n"
        for model in self.top_model_xrefs.keys():
            source, valid, toc = self.write_source_model(
                model, self.top_model_xrefs[model]
            )
            if valid:
                self.source += source

        model_class = self.get_model_class(model)
        super_args = ("%s, self" % model_class) if release.version_info[0] < 11 else ""
        opt_lang = ""
        if self.lang and self.env.user.lang != "en_US":
            opt_lang = "lang=\"%s\"" % self.lang
        model_child = self.get_child_model(model)
        self.source += SOURCE_BODY % {
            "super_args": super_args,
            "model": model,
            "model_class": model_class,
            "model_child": self.get_child_model(model),
            "test_fct_name": "test_%s" % model.replace(".", "_"),
            "opt_lang": opt_lang,
            "title": ("TEST_%s" % model.replace(".", "_").upper()),
            "title_child": (
                "TEST_%s" % self.get_child_model(model).replace(".", "_").upper() if model_child else ""
            ),
            "parent_id_name": parent_id_name,
        }

        return {
            "name": "Data created",
            "type": "ir.actions.act_window",
            "res_model": "wizard.mk.test.pyfile",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"active_id": self.id},
            "view_id": self.env.ref("mk_test_env.result_mk_test_pyfile_view").id,
            "domain": [("id", "=", self.id)],
        }

    def close_window(self):
        return {"type": "ir.actions.act_window_close"}
