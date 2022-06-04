# -*- coding: utf-8 -*-
#
# Copyright 2018-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# import os
import logging

from past.builtins import long
from z0bug_odoo import test_common

_logger = logging.getLogger(__name__)


class TestMideaQci(test_common.SingleTransactionCase):

    MIDEA_QCI_CODE = "Test-01"
    MIDEA_QCI_NAME = "Test this module"
    MIDEA_QCI_STATE = "draft"
    MIDEA_QCI_ALTER_NAME = "Test module itself"

    def setUp(self):
        super(TestMideaQci, self).setUp()

    def test_midea_no_company(self):
        model_name = "midea.qci"
        vals = {
            "code": self.MIDEA_QCI_CODE,
            "name": self.MIDEA_QCI_NAME,
            "state": self.MIDEA_QCI_STATE,
        }
        # Test the <create> function
        self.midea_no_company_id = self.create_id(model_name, vals)
        self.assertIsInstance(
            self.midea_no_company_id,
            (int, long),
            "z0bug_odoo.create_id does not return an integer id",
        )
        self.assertTrue(
            self.midea_no_company_id, "z0bug_odoo.create_id does not return a valid id"
        )
        # Now test the <browse> function
        rec = self.browse_rec(model_name, self.midea_no_company_id)
        self.assertEqual(rec.name, self.MIDEA_QCI_NAME)
        self.assertEqual(rec.state, self.MIDEA_QCI_STATE)
        # Now test the <write_rec> functon
        self.write_rec(
            model_name, self.midea_no_company_id, {"name": self.MIDEA_QCI_ALTER_NAME}
        )
        rec = self.browse_rec(model_name, self.midea_no_company_id)
        self.assertEqual(rec.name, self.MIDEA_QCI_ALTER_NAME)
        self.assertEqual(rec.state, self.MIDEA_QCI_STATE)
        _logger.info("Test %s SUCCESSFULLY ended." % __file__)
