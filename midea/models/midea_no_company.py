# -*- coding: utf-8 -*-
# Copyright 2016-19 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
from openerp import models, fields


class MideaNoCompany(models.Model):
    _name = 'midea.no_company'

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

