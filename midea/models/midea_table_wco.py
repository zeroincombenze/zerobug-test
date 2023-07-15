# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from openerp.osv import fields, orm


class MideaNoCompany(orm.Model):
    _name = "midea.table_wco"

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
                                  readonly=True),
        'company_id': fields.many2one('res.company',
                                      string='Company'),
    }

    _defaults = {
        'active': 1,
        'state': 'draft',
        'company_id': lambda self, cr, uid, ctx:
            self.pool.get('res.company')._company_default_get(
                cr, uid, 'midea.table_wco', context=ctx),

    }
