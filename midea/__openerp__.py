# -*- coding: utf-8 -*-
#
# Copyright 2018-21 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
{
    'name': 'midea',
    'summary': 'z0bug_odoo test suite',
    'version': '8.0.0.1.4',
    'category': 'Generic Modules/Accounting',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/servizi-le-imprese/',
    'depends': ['base'],
    'data': [
        'views/midea_qci_view.xml',
        'views/midea_table_wco_view.xml',
        'views/midea_menu.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
