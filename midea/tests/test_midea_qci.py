#
# Copyright 2024-25 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import os
import logging

from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


class TestMideaQci(SingleTransactionCase):

    MIDEA_QCI_CODE = "Test-01"
    MIDEA_QCI_NAME = "Test this module"
    MIDEA_QCI_STATE = "draft"
    MIDEA_QCI_ALTER_NAME = "Test module itself"
    MIDEA_QCI_MEASURE = 10.0
    MIDEA_QCI_NOTE = "<p>Test Notes</p>"

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def test_midea_no_company(self):
        _logger.info("🎺 Testing test_midea_no_company()")
        model_name = "midea.qci"
        vals = {
            "code": self.MIDEA_QCI_CODE,
            "name": self.MIDEA_QCI_NAME,
            "state": self.MIDEA_QCI_STATE,
            "measure": self.MIDEA_QCI_MEASURE,
        }
        # Test the <create> function
        self.midea_no_company = self.resource_create(model_name, vals)
        self.assertTrue(
            self.midea_no_company, "z0bug_odoo.create_id does not return a valid record"
        )
        self.assertIsInstance(
            self.midea_no_company.id,
            int,
            "z0bug_odoo.create_id does not return an integer id",
        )

        # Now test the <browse> function
        rec = self.resource_browse(self.midea_no_company.id, resource=model_name)
        self.assertEqual(rec.name, self.MIDEA_QCI_NAME)
        self.assertEqual(rec.state, self.MIDEA_QCI_STATE)
        self.assertEqual(rec.measure, self.MIDEA_QCI_MEASURE)
        # Now test the <write> functon
        self.resource_write(
            model_name,
            self.midea_no_company.id,
            values={
                "name": self.MIDEA_QCI_ALTER_NAME,
                "note": self.MIDEA_QCI_NOTE,
            },
        )
        rec = self.resource_browse(self.midea_no_company.id, resource=model_name)
        self.assertEqual(rec.name, self.MIDEA_QCI_ALTER_NAME)
        self.assertEqual(rec.state, self.MIDEA_QCI_STATE)
        self.assertEqual(rec.note, self.MIDEA_QCI_NOTE)
        _logger.info("Test %s SUCCESSFULLY ended." % __file__)
