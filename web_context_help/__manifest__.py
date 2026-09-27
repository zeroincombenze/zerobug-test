# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
{
    "name": "Context help",
    "version": "12.0.1.0.0",
    "category": "Hidden/Tools",
    "summary": "Context help button, pages written in RST by each module",
    "author": "Zeroincombenze srls",
    "website": "https://github.com/zeroincombenze/zerobug-test",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "depends": ["web"],
    "external_dependencies": {"python": ["docutils"]},
    "data": [
        "security/ir.model.access.csv",
        "views/context_help_views.xml",
        "views/assets.xml",
    ],
    "qweb": ["static/src/v11_14/control_panel.xml"],
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
