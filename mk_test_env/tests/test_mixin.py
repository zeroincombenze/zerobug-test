#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)
PARTNER_1 = {
    'name': 'Prima Alpha S.p.A.',
    'street': 'Via I Maggio, 101',
    'country_id': 'base.it',
    'zip': '20022',
}


class TestMixin(common.TransactionCase):
    def setUp(self):
        super(TestMixin, self).setUp()
        self.wizard_mk_test_env = self.env['wizard.make.test.environment'].create({})
        self.wizard_mk_test_pyfile = self.env['wizard.mk.test.pyfile'].create({})

    def tearDown(self):
        super(TestMixin, self).tearDown()

    def test_mk_test_env(self):
        _logger.info("🎺 Testing test_mk_test_env()")
        wizard = self.wizard_mk_test_env

        for distro, tres in (('odoo_ce', '14.0'),
                             ('odoo_ce', '14.0'),
                             ('zero', 'zero14'),
                             ('librerp', 'librerp14'),
                             ('powerp', 'librerp14'),
                             ):
            wizard.distro = distro
            result = wizard.get_tgtver()
            self.assertEqual(
                result, tres,
                msg='Invalid distro version: expected %s, found %s' % (tres, result))

        tres = PARTNER_1
        result = wizard.get_test_values('res.partner', 'z0bug.res_partner_1')
        for field in tres.keys():
            self.assertEqual(
                result[field], tres[field],
                msg='Invalid test value %s: expected %s, found %s' % (
                    field, tres[field], result[field]))

    def test_mk_test_pyfile(self):
        _logger.info("🎺 Testing test_mk_test_pyfile()")
        wizard = self.wizard_mk_test_pyfile

        for oca_coding, tres in ((True, '14.0'),
                                 (False, 'librerp14'),
                                 ):
            wizard.oca_coding = oca_coding
            result = wizard.get_tgtver()
            self.assertEqual(
                result, tres,
                msg='Invalid distro version: expected %s, found %s' % (tres, result))

        dependecies = 'base,base_setup,bus,mail,web,web_tour'.split(',')
        tres = set(self.env['ir.module.module'].search([('name', 'in', dependecies)]))
        result = wizard.get_dependencies('mail')
        self.assertEqual(
            result, tres,
            msg='Invalid dependencies: expected %s, found %s' % (tres, result))
        tres = set(dependecies)
        result = set(wizard.get_dependency_names('mail'))
        self.assertEqual(
            result, tres,
            msg='Invalid dependencies: expected %s, found %s' % (tres, result))

        tres = PARTNER_1
        result = wizard.get_test_values('res.partner', 'z0bug.res_partner_1')
        for field in tres.keys():
            self.assertEqual(
                result[field], tres[field],
                msg='Invalid test value %s: expected %s, found %s' % (
                    field, tres[field], result[field]))
