# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
{
    "name": "midea",
    "summary": "z0bug_odoo test suite",
    "version": "8.0.0.1.6",
    "category": "Generic Modules/Accounting",
    "author": "SHS-AV s.r.l.",
    "website": "https://github.com/OCA/l10n-italy",
    "depends": ["base"],
    "data": [
        "views/midea_qci_view.xml",
        "views/midea_table_wco_view.xml",
        "views/midea_menu.xml",
        "security/ir.model.access.csv",
        "data/midea_qci.xml",
    ],
    "installable": True,
    "maintainer": "Antonio Maria Vigliotti",
    "development_status": "Beta",
}
