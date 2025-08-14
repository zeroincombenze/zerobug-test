# Copyright 2020-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from datetime import datetime
from odoo import fields, models


class MideaNoCompany(models.Model):
    _name = "midea.table_wco"
    _description = "Midea with Company"

    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    def _default_rank(self):
        return 16

    def _default_amount(self):
        return 10.0

    def _default_date(self):
        return datetime.date(datetime.today())

    def _default_partners(self):
        return self.env.user

    name = fields.Char("Name", required=True, translate=True)
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
    rank = fields.Integer("Rank", default=_default_rank, help="Integer field")
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        default=_default_amount,
        help="Monetary field",
    )
    date = fields.Date(string='Date', default=_default_date, help="Date field")
    partner_ids = fields.One2many(
        comodel_name="res.partner",
        inverse_name="testenv_id",
        default=_default_partners,
        string="Stakeholders",
    )
    image = fields.Binary("Image", attachment=True)
    description = fields.Text("Description", help="Text field")

    def action_done(self):
        for rec in self:
            rec.state = "done"

    def action_draft(self):
        for rec in self:
            rec.state = "draft"

    def action_cancel(self):
        for rec in self:
            rec.state = "cancel"
