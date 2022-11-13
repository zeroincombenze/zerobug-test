# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from odoo import fields, models


class MideaNoCompany(models.Model):
    _name = "midea.table_wco"

    name = fields.Char("name", required=True, translate=True)
    active = fields.Boolean("Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        "State",
        required=True,
        readonly=True,
        default="draft",
    )
    company_id = fields.Many2one("res.company", string="Company")
