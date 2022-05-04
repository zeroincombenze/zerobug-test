#
# Copyright 2018-20 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import logging

from past.builtins import long
from z0bug_odoo import test_common

_logger = logging.getLogger(__name__)


class TestMidea(test_common.SingleTransactionCase):

    MIDEA_TABLE_WCO_NAME = "Mario Rossi"
    MIDEA_TABLE_WCO_STATE = "draft"
    MIDEA_TABLE_WCO_ALTER_NAME = "Giovanni Bianchi"

    def setUp(self):
        super(TestMidea, self).setUp()
        self.company_id = self.set_test_company()

    def test_midea_table_wco(self):
        # Check for valid company
        company = self.browse_rec("res.company", self.company_id)
        self.assertEqual(company.name, "Test Company")
        #
        model_name = "midea.table_wco"
        vals = {
            "name": self.MIDEA_TABLE_WCO_NAME,
            "state": self.MIDEA_TABLE_WCO_STATE,
            "company_id": self.company_id,
        }
        # Test the <create> function
        self.midea_table_wco_id = self.create_id(model_name, vals)
        self.assertIsInstance(
            self.midea_table_wco_id,
            (int, long),
            "z0bug_odoo.create_id does not return an integer id",
        )
        self.assertTrue(
            self.midea_table_wco_id, "z0bug_odoo.create_id does not return a valid id"
        )
        # Now test the <browse> function
        rec = self.browse_rec(model_name, self.midea_table_wco_id)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_NAME)
        self.assertEqual(rec.state, self.MIDEA_TABLE_WCO_STATE)
        self.assertEqual(rec.company_id.id, self.company_id)
        # Now test the <write_rec> functon
        self.write_rec(
            model_name,
            self.midea_table_wco_id,
            {"name": self.MIDEA_TABLE_WCO_ALTER_NAME},
        )
        rec = self.browse_rec(model_name, self.midea_table_wco_id)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_ALTER_NAME)
        self.assertEqual(rec.state, self.MIDEA_TABLE_WCO_STATE)
        self.assertEqual(rec.company_id.id, self.company_id)
        _logger.info("Test %s SUCCESSFULLY ended." % __file__)
