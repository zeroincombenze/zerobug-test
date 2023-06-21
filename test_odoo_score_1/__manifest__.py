# -*- coding: utf-8 -*-
#
# Copyright 2022-23 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
{
    "name": "Test Odoo score",
    "summary": "odoo_score test suite",
    "version": "10.0.2.0.6",
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
    "version_external_dependencies": ["odoo_score==2.0.6"],
    "depends": [
        "base", "account", "account_cancel", "product", "sale",
    ],
    "data": [
    ],
    "installable": True,
    "maintainer": "Antonio Maria Vigliotti",
    "development_status": "Alpha",
    "pre_init_hook": "check_4_depending",
}
