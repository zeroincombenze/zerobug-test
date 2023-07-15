#
# Copyright 2018-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import os
import logging

from past.builtins import long

from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


class TestMidea(SingleTransactionCase):

    MIDEA_TABLE_WCO_NAME = "Mario Rossi"
    MIDEA_TABLE_WCO_STATE = "draft"
    MIDEA_TABLE_WCO_ALTER_NAME = "Giovanni Bianchi"

    def setUp(self):
        super().setUp()
        self.company = self.default_company()

    def tearDown(self):
        super().tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def test_midea_table_wco(self):
        _logger.info("🎺 Testing test_midea_table_wco()")
        model_name = "midea.table_wco"
        vals = {
            "name": self.MIDEA_TABLE_WCO_NAME,
            "state": self.MIDEA_TABLE_WCO_STATE,
            "company_id": self.company.id,
        }
        # Test the <create> function
        self.midea_table_wco = self.resource_create(model_name, vals)
        self.assertTrue(
            self.midea_table_wco, "z0bug_odoo.create_id does not return a valid record"
        )
        self.assertIsInstance(
            self.midea_table_wco.id,
            (int, long),
            "z0bug_odoo.create_id does not return an integer id",
        )

        # Now test the <browse> function
        rec = self.resource_browse(self.midea_table_wco.id, resource=model_name)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_NAME)
        self.assertEqual(rec.state, self.MIDEA_TABLE_WCO_STATE)
        self.assertEqual(rec.company_id, self.company)
        # Now test the <write_rec> functon
        self.resource_write(
            model_name,
            self.midea_table_wco.id,
            values={"name": self.MIDEA_TABLE_WCO_ALTER_NAME},
        )
        rec = self.resource_browse(self.midea_table_wco.id, resource=model_name)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_ALTER_NAME)
        self.assertEqual(rec.state, self.MIDEA_TABLE_WCO_STATE)
        self.assertEqual(rec.company_id, self.company)
        _logger.info("Test %s SUCCESSFULLY ended." % __file__)
