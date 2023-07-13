# -*- coding: utf-8 -*-
#
# Copyright 2016-22 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
import logging

from z0bug_odoo import z0bug_odoo_lib
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


class TestMidea(SingleTransactionCase):
    def setUp(self):
        super(TestMidea, self).setUp()
        self.debug_level = 0

    def test_res_partner(self):
        res = z0bug_odoo_lib.Z0bugOdoo().get_test_values(
            "res.partner", "z0bug.res_partner_1"
        )
        _logger.info("Test %s SUCCESSFULLY ended." % __file__)
        self.assertEqual(res["name"], "Prima Alpha S.p.A.")
        self.assertEqual(res["zip"], "20022")
        self.assertEqual(res["city"], "Castano Primo")
