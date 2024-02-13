#
# Copyright 2020-24 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from odoo import fields, models


class MideaQci(models.Model):
    _name = "midea.qci"

    code = fields.Char("Code", required=True)
    name = fields.Char("Name", required=True, translate=True)
    active = fields.Boolean("Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancel", "Canceled")],
        "State",
        required=True,
        readonly=True,
        default="draft",
    )
