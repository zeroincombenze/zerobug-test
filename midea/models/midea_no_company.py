# -*- coding: utf-8 -*-
#
# Copyright 2018-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from openerp.osv import orm, fields


class MideaNoCompany(orm.Model):
    _name = 'midea.no_company'

    _columns = {
        'name': fields.char('Name',
                            required=True,
                            translate=True),
        'active': fields.boolean('Active'),
        'state': fields.selection([('draft', 'Draft'),
                                   ('confirmed', 'Confirmed'),
                                   ('deleted', 'Deleted')],
                                  'State',
                                  required=True,
                                  readonly=True)
    }

    _defaults = {
        'active': 1,
        'state': 'draft',
    }
