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
    "version": "16.0.1.0.1",
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
    ],
    "assets": {
        "web.assets_backend": [
            "web_context_help/static/src/v16/context_help_service.js",
            "web_context_help/static/src/v16/control_panel.js",
            "web_context_help/static/src/v16/control_panel.xml",
            "web_context_help/static/src/v16/context_help.scss",
        ],
    },
    "maintainer": "Antonio M. Vigliotti <antoniomaria.vigliotti@gmail.com>",
    "installable": True,
}
