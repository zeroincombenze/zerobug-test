# -*- coding: utf-8 -*-
# Copyright 2016-19 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from odoo import models, fields


class MideaPartner(models.Model):
    _name = 'midea.partner'

    name = fields.Char('name',
                       required=True,
                       translate=True)
    active = fields.Boolean('Active',
                            default=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirmed', 'Confirmed')],
                             'State',
                             required=True,
                             readonly=True,
                             default='draft')
