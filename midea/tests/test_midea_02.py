# -*- coding: utf-8 -*-
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

    MIDEA_TABLE_WCO_NAME = 'Mario Rossi'
    MIDEA_TABLE_WCO_STATE = 'draft'
    MIDEA_TABLE_WCO_ALTER_NAME = 'Giovanni Bianchi'

    def setUp(self):
        super(TestMidea, self).setUp()
        self.company_id = self.set_test_company()

    def test_midea_table_wco(self):
        model_name = 'midea.table_wco'
        vals = {
            'name': self.MIDEA_TABLE_WCO_NAME,
            'state': self.MIDEA_TABLE_WCO_STATE,
            'company_id': self.company_id
        }
        # Test the create function
        self.midea_table_wco_id = self.create_id(
            model_name, vals)
        self.assertIsInstance(
            self.midea_table_wco_id,
            (int, long),
            'z0bug_odoo.create_id does not return an integer id')
        self.assertTrue(self.midea_table_wco_id,
                        'z0bug_odoo.create_id does not return a valid id')
        # Now test browse function
        rec = self.browse_rec(model_name, self.midea_table_wco_id)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_NAME)
        # Now test write_rec functon
        self.write_rec(model_name, self.midea_table_wco_id,
                      {'name': self.MIDEA_TABLE_WCO_ALTER_NAME})
        rec = self.browse_rec(model_name, self.midea_table_wco_id)
        self.assertEqual(rec.name, self.MIDEA_TABLE_WCO_ALTER_NAME)
