# -*- coding: utf-8 -*-
# Copyright 2016-19 Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from openerp.osv import orm, fields


class MideaNoCompany(orm.Model):
    _name = 'midea.no_company'

    _columns = {
        'name': fields.char('Name',
                            required=True,
                            translate=True),
        'active': fields.boolean('Active',
                                 default=True),
        'state': fields.selection([('draft', 'Draft'),
                                   ('confirmed', 'Confirmed')],
                                  'State',
                                  required=True,
                                  readonly=True,
                                  default='draft')
    }
