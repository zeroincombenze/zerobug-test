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

    MIDEA_PARTNER_NAME = 'Mario Rossi'
    MIDEA_PARTNER_STATE = 'draft'
    MIDEA_PARTNER_ALTER_NAME = 'Giovanni Bianchi'

    def setUp(self):
        super(TestMidea, self).setUp()

    def test_midea_partner(self):
        model_name = 'midea.partner'
        vals = {
            'name': self.MIDEA_PARTNER_NAME,
            'state': self.MIDEA_PARTNER_STATE,
        }
        # Test the create function
        self.midea_partner_id = self.create_id(
            model_name, vals)
        self.assertIsInstance(
            self.midea_partner_id,
            (int, long),
            'z0bug_odoo.create_id does not return an integer id')
        self.assertTrue(self.midea_partner_id,
                        'z0bug_odoo.create_id does not return a valid id')
        # Now test browse function
        rec = self.browse_rec(model_name, self.midea_partner_id)
        self.assertEqual(rec.name, self.MIDEA_PARTNER_NAME)
        # Now test write_rec functon
        self.write_rec(model_name, self.midea_partner_id,
                      {'name': self.MIDEA_PARTNER_ALTER_NAME})
        rec = self.browse_rec(model_name, self.midea_partner_id)
        self.assertEqual(rec.name, self.MIDEA_PARTNER_ALTER_NAME)
