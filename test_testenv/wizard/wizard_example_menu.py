#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# from past.builtins import basestring
from datetime import datetime, timedelta
from random import random, randint

from odoo import fields, models, api, _
# from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import odoo.release as release
    except ImportError:
        release = ""


class WizardExamplMenu(models.TransientModel):
    _name = "wizard.example.menu"
    _description = "Example of wizard from Menu"

    numrecords = fields.Integer("# of recors to create")

    @api.onchange("numrecords")
    def _onchange_numrecords(self):
        if self.numrecords < 0:
            self.numrecords = 0
        elif self.numrecords > 3:
            self.numrecords = 3

    def do_example(self):

        if not self.numrecords:
            # Case 1: no record, show the same windows with "no results"
            return {
                "name": "Wizard from menu",
                "type": "ir.actions.act_window",
                "res_model": "wizard.example.menu",
                "view_type": "form",
                "view_mode": "form",
                "res_id": self.id,
                "target": "new",
                "context": {"active_id": self.id},
                "view_id":
                    self.env.ref("test_testenv.result_wizard_example_menu_view").id,
                "domain": [("id", "=", self.id)],
            }

        fnames = ("Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Omicron")
        lnames = ("Red", "Orange", "Brown", "Green", "Turquoise", "Black", "White")
        descr = ("I was born in Caserta", "", "We live in Turin")
        dates = (
            (datetime.today() - timedelta(days=1)).date(),
            (datetime.today() - timedelta(days=5)).date(),
            (datetime.today() - timedelta(days=14)).date(),
        )
        refdate = (datetime.now() - timedelta(days=27))
        partners = [x.id for x in self.env["res.partner"].search(
            ["|",
             ("name", "like", "Prima Alpha"),
             ("name", "like", "Latte Beta")
             ]
        )]

        rec_ids = []
        for nr in range(self.numrecords):
            vals = {
                "name": "%s %s" % (fnames[randint(0, 6)], lnames[randint(0, 6)]),
                "description": descr[nr],
                "active": True,
                "state": "draft",
                "rank": nr + 1,
                "amount": random() * 1000 if nr else 1234.5,
                "measure": random() * 90 if nr != 1 else 98.7,
                "created_dt": datetime(
                    refdate.year,
                    refdate.month,
                    nr + 1,
                    nr + 10,
                    nr * 10,
                    59 - (nr * 7),
                    0
                ),
                "updated_dt": datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S"),
                "date": dates[nr],
            }
            if nr == 2:
                vals["partner_ids"] = [(6, 0, partners)]
            record = self.env["testenv.all.fields"].create(vals)
            rec_ids.append(record.id)
        # Case 2: show result records
        return {
            "name": _("Example Records"),
            "view_type": "form",
            "view_mode": "form,tree",
            "res_model": "testenv.all.fields",
            "domain": [("id", "in", rec_ids)],
            "type": "ir.actions.act_window",
            "view_id": False,
            "views":
                [(self.env.ref("test_testenv.testenv_all_fields_tree").id, "tree"),
                 (self.env.ref("test_testenv.testenv_all_fields_form").id, "form")],
        }

    def close_window(self):
        return {"type": "ir.actions.act_window_close"}
