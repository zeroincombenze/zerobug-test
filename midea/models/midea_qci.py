# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from openerp.osv import orm, fields


class MideaQci(orm.Model):
    _name = 'midea.qci'

    _columns = {
        'code': fields.char('Code', required=True),
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
