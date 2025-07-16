# -*- coding: utf-8 -*-
#
# Copyright 2018-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
{
    "name": "midea",
    "version": "10.0.0.1.9",
    "category": "Generic Modules/Accounting",
    "summary": "Migration and backporting test suite",
    "author": "SHS-AV s.r.l.",
    "website": "https://github.com/OCA/l10n-italy",
    "development_status": "Beta",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",
    ],
    "data": [
        "views/midea_qci_view.xml",
        "views/midea_table_wco_view.xml",
        "views/midea_menu.xml",
        "security/ir.model.access.csv",
        "data/midea_qci.xml",
        "data/midea_table_wco.xml",
    ],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
