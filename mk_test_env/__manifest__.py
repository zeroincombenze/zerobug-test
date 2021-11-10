# -*- coding: utf-8 -*-
#
# Copyright 2019-21 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
{
    'name': 'Manage Test Environment',
    'summary': 'Create or update test environment',
    'version': '10.0.0.6.4',
    'category': 'Tools',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/servizi-le-imprese/',
    'license': 'LGPL-3',
    'depends': [
        'base',
    ],
    'external_dependencies': {
        'python': [
            'zerobug',
            'z0bug_odoo',
            'os0',
            'future',
            'python_plus',
            'past',     # TODO: pylint bug, it is to remove
        ],
    },
    'data': [
        # 'security/ir.model.access.csv',
        'views/menu.xml',
        'wizard/wizard_mk_test_env_view.xml',
        # 'wizard/wizard_cleanup_test_env_view.xml',
    ],
    'installable': True,
    'maintainer': 'Zeroincombenze (R)',
    'development_status': 'Beta',
}
