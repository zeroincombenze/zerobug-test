#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
{
    "name": "Manage Test Environment",
    "summary": "Create or update test environment",
    "version": "12.0.0.7.7",
    "category": "Tools",
    "author": "SHS-AV s.r.l.",
    "website": "https://github.com/OCA/l10n-italy",
    "license": "LGPL-3",
    "depends": [
        "base",
        "product",      # to test TestEnv
    ],
    "external_dependencies": {
        "python": [
            "clodoo",
            "zerobug",
            "z0bug_odoo",
            "os0",
            "future",
            "python_plus",
            "past",  # TODO: pylint bug, it is to remove
        ],
    },
    "version_external_dependencies": [
        "clodoo>=2.0.9",
        "zerobug>=2.0.14",
        "z0bug_odoo>=2.0.17",
        "os0>2.0.0",
        "python_plus>=2.0.12"
    ],
    "data": [
        # 'security/ir.model.access.csv',
        "views/menu.xml",
        "wizard/wizard_mk_test_env_view.xml",
        "wizard/wizard_mk_test_pyfile_view.xml",
        "wizard/wizard_get_test_data_view.xml",
    ],
    #  EXAMPLE! "qweb": ["static/src/xml/example.xml"],
    "installable": True,
    "maintainer": "Zeroincombenze (R)",
    "development_status": "Beta",
    "pre_init_hook": "check_4_depending",
}
