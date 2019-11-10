#
# Copyright 2018-19 - SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
#
# The purpose of this test module is validate the z0bug_odoo package.
#
import base64
import os

from z0bug_odoo import test_common


class TestMidea(test_common.SingleTransactionCase):

    MIDEA_NO_COMPANY_NAME = 'Mario Rossi'
    MIDEA_NO_COMPANY_STATE = 'draft'
    MIDEA_NO_COMPANY_ALTER_NAME = 'Giovanni Bianchi'

    def setUp(self):
        super(TestMidea, self).setUp()

    def test_midea_no_company(self):
        model_name = 'midea.no_company'
        vals = {
            'name': self.MIDEA_NO_COMPANY_NAME,
            'state': self.MIDEA_NO_COMPANY_STATE,
        }
        # Test the <create> function
        self.midea_no_company_id = self.create_id(
            model_name, vals)
        self.assertIsInstance(
            self.midea_no_company_id,
            (int, long),
            'z0bug_odoo.create_id does not return an integer id')
        self.assertTrue(self.midea_no_company_id,
                        'z0bug_odoo.create_id does not return a valid id')
        # Now test the <browse> function
        rec = self.browse_rec(model_name, self.midea_no_company_id)
        self.assertEqual(rec.name, self.MIDEA_NO_COMPANY_NAME)
        self.assertEqual(rec.state, self.MIDEA_NO_COMPANY_STATE)
        # Now test the <write_rec> functon
        self.write_rec(model_name, self.midea_no_company_id,
                      {'name': self.MIDEA_NO_COMPANY_ALTER_NAME})
        rec = self.browse_rec(model_name, self.midea_no_company_id)
        self.assertEqual(rec.name, self.MIDEA_NO_COMPANY_ALTER_NAME)
        self.assertEqual(rec.state, self.MIDEA_NO_COMPANY_STATE)

