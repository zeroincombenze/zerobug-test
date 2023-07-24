# -*- coding: utf-8 -*-
import os
import logging
from .testenv import MainTest as SingleTransactionCase
import odoo_score


_logger = logging.getLogger(__name__)


TEST_SETUP_LIST = [
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super(MyTest, self).setUp()
        self.debug_level = 0

    def tearDown(self):
        super(MyTest, self).tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):                   # pragma: no cover
            # Save test environment, so it is available to use
            self.env.cr.commit()                       # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def _test_global_function(self):
        self.assertTrue(odoo_score.check_object_name("a.b"))
        self.assertFalse(odoo_score.check_object_name("a-b"))

    def _test_import_models(self):
        # del odoo_score
        try:
            from odoo_score import models
            self.assertTrue(models, "Imported models from odoo_score")
        except BaseException:
            self.assertTrue(models, "Imported models from odoo_score")
            return
        self.assertTrue(hasattr(models.Model, "_abstract"), "models.Model attribute")
        self.assertTrue(hasattr(models.Model, "_transient"), "models.Model attribute")

    def test_odoo_score(self):
        self._test_global_function()
        self._test_import_models()
