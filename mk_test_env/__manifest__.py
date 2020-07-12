# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    'name': 'Manage Test Environment',
    'summary': 'Create, update or clean-up test environment',
    'version': '12.0.0.4',
    'category': 'Tools',
    'author': 'SHS-AV s.r.l.',
    'website': 'https://www.zeroincombenze.it/servizi-le-imprese/',
    'license': 'LGPL-3',
    'depends': [
        'base'
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
        'views/menu.xml',
        'wizard/wizard_mk_test_env_view.xml',
        'wizard/wizard_cleanup_test_env_view.xml',
    ],
    'installable': True,
    'maintainer': 'Zeroincombenze (R)',
    'development_status': 'Alpha',
}
