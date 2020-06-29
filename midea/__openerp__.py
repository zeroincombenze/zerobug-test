# -*- coding: utf-8 -*-
#
# Copyright 2018-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'midea',
    'summary': 'z0bug_odoo test suite',
    'version': '8.0.0.1.3',
    'category': 'Generic Modules/Accounting',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/',
    'depends': ['base'],
    'data': [
        'views/midea_no_company_view.xml',
        'views/midea_table_wco_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}

