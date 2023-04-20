import os
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


TEST_SETUP_LIST = []


class MyTest(SingleTransactionCase):
    def setUp(self):
        super().setUp()
        self.debug_level = 2

    def tearDown(self):
        super().tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):  # pragma: no cover
            # Save test environment, so it is available to use
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def test_odoo_score(self):
        pass
