#
# Copyright 2018-20 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import logging

from z0bug_odoo import test_common, z0bug_odoo_lib

_logger = logging.getLogger(__name__)


class TestMidea(test_common.SingleTransactionCase):

    def setUp(self):
        super(TestMidea, self).setUp()

    def test_res_partner(self):
        res = z0bug_odoo_lib.Z0bugOdoo().get_test_values(
            'res.partner', 'z0bug.res_partner_1')
        _logger.info(
            'Test %s SUCCESSFULLY ended.' % __file__)
        self.assertEqual(res['name'], 'Prima Distribuzione S.p.A.')
        self.assertEqual(res['zip'], '20022')
        self.assertEqual(res['city'], 'Castano Primo')
