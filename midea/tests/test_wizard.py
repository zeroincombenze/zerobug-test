# -*- coding: utf-8 -*-
#
# Copyright 2016-18 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import os
import logging

from .envtest import EnvTest

_logger = logging.getLogger(__name__)


class TestMideaWizard(EnvTest):
    def setUp(self):
        super(TestMideaWizard, self).setUp()
        self.iso_code = "it_IT"

    def tearDown(self):
        super(TestMideaWizard, self).tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def test_wizard(self):
        """Test the EnvTest wizard functions"""
        # We engage language transaltion wizard with "it_IT" language
        # see "<ODOO_PATH>/addons/base/module/wizard/base_language_install*"
        _logger.info("🎺 Testing wizard.lang_install()")
        act_windows = self.wizard(
            module="base",
            action_name="action_view_base_language_install",
            # act_windows=None,
            default={
                "lang": self.iso_code,
                "overwrite": False,
            },
            button_name="lang_install",
        )
        self.assertTrue(
            self.is_action(act_windows),
            "No action returned by language install"
        )
        # Now we test the close message
        self.wizard(
            act_windows=act_windows
        )
        self.assertTrue(
            self.env["res.lang"].search([("code", "=", self.iso_code)]),
            "No language %s loaded!" % self.iso_code
        )
