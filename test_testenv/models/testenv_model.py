# -*- coding: utf-8 -*-
# Copyright 2018-23 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
from datetime import datetime
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    testenv_id = fields.Many2one("testenv.all.fields")


class TestenvAllFields(models.Model):
    _name = "testenv.all.fields"

    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    def _default_rank(self):
        return 16

    def _default_measure(self):
        return 1.0

    def _default_amount(self):
        return 10.0

    def _default_created_dt(self):
        return datetime.now()

    def _default_date(self):
        return datetime.date(datetime.today())

    def _default_partners(self):
        return self.env.user

    name = fields.Char("Name", help="Char field")
    active = fields.Boolean("Active", default=True, help="Boolean field")
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed")],
        "State",
        default="draft",
        help="Selection field",
    )
    company_id = fields.Many2one("res.company", string="Company", help="Company field")
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=_default_currency,
    )
    description = fields.Text("Description", help="Text field")
    rank = fields.Integer("Rank", default=_default_rank, help="Integer field")
    amount = fields.Monetary(
        string="Amount",
        currency_field="currency_id",
        default=_default_amount,
        help="Monetary field",
    )
    measure = fields.Float("Amount", default=_default_measure, help="Float field")
    date = fields.Date(string='Date', default=_default_date, help="Date field")
    created_dt = fields.Datetime(
        string='Created timestamp', default=_default_created_dt, help="Datetime field"
    )
    updated_dt = fields.Datetime(string='Delivery timestamp', help="Datetime field")
    attachment = fields.Binary("Attachemnt")
    webpage = fields.Html("Html")
    partner_ids = fields.One2many(
        comodel_name="res.partner",
        inverse_name="testenv_id",
        default=_default_partners,
        string="Partners",
    )
    product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Products",
    )
