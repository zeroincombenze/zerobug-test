#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from past.builtins import basestring

from odoo import fields, models
from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import odoo.release as release
    except ImportError:
        release = ""
# from .mixin import BaseTestMixin

import python_plus
# from clodoo import transodoo
from os0 import os0
from z0bug_odoo import z0bug_odoo_lib

VERSION_ERROR = 'Invalid package version! Use: pip install "%s>=%s" -U'


class WizardGetTestData(models.TransientModel):
    _name = "wizard.get.test.data"
    _description = "Print test data example"
    _inherit = ["base.test.mixin"]

    source = fields.Text("Source code")
    model2export = fields.Many2one(
        comodel_name="ir.model",
        string="Models to expport",
    )

    def assure_types(self, resource, vals):
        if resource not in self.struct:
            self.struct[resource] = self.env[resource].fields_get()
        for field in list(vals.keys()).copy():
            if vals[field] is None or vals[field] in ("None", r"\N"):
                del vals[field]
                continue
            if field not in self.struct[resource]:
                del vals[field]
                continue
            ftype = self.struct[resource][field]["type"]
            if ftype == "boolean":
                vals[field] = os0.str2bool(vals[field], False)
            elif ftype in ("float", "monetary") and isinstance(
                vals[field], basestring
            ):
                vals[field] = eval(vals[field])
            elif ftype in ("date", "datetime"):
                vals[field] = python_plus.compute_date(vals[field])
            elif (
                ftype in ("many2one", "one2many", "many2many", "integer")
                and isinstance(vals[field], basestring)
                and (
                    vals[field].isdigit()
                    or vals[field].startswith("-")
                    and vals[field][1:].isdigit()
                )
            ):
                vals[field] = int(vals[field])
        return vals

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
        # self.diff_ver("2.0.0", "clodoo", "transodoo")
        self.diff_ver("2.0.0", "os0", "os0")
        self.diff_ver("2.0.0", "python_plus", "python_plus")

        if not self.model2export:
            raise UserError("Missed model to export")
        self.struct = {}
        resource = self.model2export.model
        title = "TEST_%s" % resource.replace(".", "_").upper()
        source = "%s = {\n" % title
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(resource)
        for xref in xrefs:
            source += "    \"%s\": {\n" % xref
            vals = self.assure_types(
                resource,
                z0bug_odoo_lib.Z0bugOdoo().get_test_values(resource, xref)
            )
            for (field, value) in vals.items():
                if field in ("id", "currency_id"):
                    continue
                if field not in self.struct[resource]:
                    continue
                if self.struct[resource][field]["type"] in (
                    "integer",
                    "float",
                    "monetary",
                ):
                    source += "        \"%s\": %s,\n" % (field, value)
                elif self.struct[resource][field]["type"] == "boolean":
                    source += "        \"%s\": %s,\n" % (
                        field,
                        "True" if value else "False",
                    )
                else:
                    source += "        \"%s\": \"%s\",\n" % (field, value)
            source += "    },\n"
        source += "}\n"
        self.source = source

        return {
            "name": "Data created",
            "type": "ir.actions.act_window",
            "res_model": "wizard.get.test.data",
            "view_type": "form",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"active_id": self.id},
            "view_id": self.env.ref("mk_test_env.result_get_test_data_view").id,
            "domain": [("id", "=", self.id)],
        }

    def close_window(self):
        return {"type": "ir.actions.act_window_close"}
