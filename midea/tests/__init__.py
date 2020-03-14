# -*- coding: utf-8 -*-
#
# Copyright 2018-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License APGL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from . import test_midea_no_company
from . import test_midea_table_wco
from . import test_res_partner

checks = [
    test_midea_no_company,
    test_midea_table_wco,
    test_res_partner
]
