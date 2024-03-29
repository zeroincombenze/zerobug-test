# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
{
    "name": "testenv",
    "summary": "z0bug_odoo test suite",
    "version": "10.0.2.0.14",
    "category": "Generic Modules/Accounting",
    "author": "SHS-AV s.r.l.",
    "website": "https://github.com/OCA/l10n-italy",
    "external_dependencies": {
        "python": [
            "future",
            "python_plus",
            "past",  # TODO: pylint bug, it is to remove
        ],
    },
    "version_external_dependencies": ["z0bug_odoo==2.0.15"],
    "depends": [
        "base",
        "account",
        "account_cancel",
        "product",
        "sale",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/testenv_model_view.xml",
        "wizard/wizard_example_menu.xml",
    ],
    "installable": True,
    "maintainer": "Antonio Maria Vigliotti",
    "development_status": "Production/Stable",
    "pre_init_hook": "check_4_depending",
}
