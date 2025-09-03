# -*- coding: utf-8 -*-
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from openerp import fields, models


class MideaNoCompany(models.Model):
    _name = "midea.table_wco"

    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    name = fields.Char("name", required=True, translate=True)
    active = fields.Boolean("Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Confirmed"), ("cancel", "Cancelled")],
        "State",
        required=True,
        readonly=True,
        default="draft",
    )
    company_id = fields.Many2one("res.company", string="Company")
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=_default_currency,
    )

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
