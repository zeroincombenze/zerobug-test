#
# Copyright 2022-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from datetime import datetime
from odoo import fields, models


class MideaQci(models.Model):
    _name = "midea.qci"
    _description = "Midea QCI (non company)"

    def _default_measure(self):
        return 1.0

    def _default_measured_ts(self):
        return datetime.now()

    code = fields.Char("Code", required=True, index=True)
    name = fields.Char("Name", required=True, translate=True)
    active = fields.Boolean("Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("cancel", "Canceled")],
        "State",
        required=True,
        default="draft",
    )
    measure = fields.Float("Measure", default=_default_measure, help="Float field")
    measured_ts = fields.Datetime(
        string='Measured on',
        default=_default_measured_ts,
        help="Datetime field")
    note = fields.Html("Notes")
    product_ids = fields.Many2many(
        comodel_name="product.product",
        string="Products",
    )
    attachment = fields.Binary("Attachment")
    sequence = fields.Integer("Sequence", default=16)
