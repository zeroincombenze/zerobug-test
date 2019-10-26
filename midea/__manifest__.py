# -*- coding: utf-8 -*-
#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
{
    'name': 'midea',
    'summary': 'z0bug_odoo test suite',
    'version': '10.0.0.1.0',
    'category': 'Generic Modules/Accounting',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': ['base'],
    'data': [
        'views/midea_partner_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
