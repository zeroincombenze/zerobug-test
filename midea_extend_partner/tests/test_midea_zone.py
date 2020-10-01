# -*- coding: utf-8 -*-
#
# Copyright 2018-20 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#

from z0bug_odoo import test_common


class TestMidea(test_common.SingleTransactionCase):

    def setUp(self):
        super(TestMidea, self).setUp()

    def test_midea_no_company(self):
        model_name = 'res.partner'
        partner1 = self.browse_ref('base.partner_1')
        self.assertFalse(partner1.zone)
        self.write_rec(model_name, partner1.id, {'zone': 'XX'})
        partner1 = self.browse_ref('base.partner_1')
        self.assertTrue(partner1.zone)
