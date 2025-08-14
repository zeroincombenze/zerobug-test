#
# Copyright 2024-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    testenv_id = fields.Many2one("midea.table_wco")
