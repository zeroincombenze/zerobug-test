# -*- coding: utf-8 -*-
import os
import logging
from .testenv import MainTest as SingleTransactionCase

_logger = logging.getLogger(__name__)


TEST_ACCOUNT_PAYMENT_TERM = {
    "z0bug.payment_0": {},
    "z0bug.payment_1": {},
    "z0bug.payment_2": {},
    "z0bug.payment_3": {},
    "z0bug.payment_4": {},
    "z0bug.payment_5": {},
}
TEST_ACCOUNT_PAYMENT_TERM_LINE = {
    "z0bug.payment_0_9": {},
    "z0bug.payment_1_9": {},
    "z0bug.payment_2_1": {},
    "z0bug.payment_2_9": {},
    "z0bug.payment_3_9": {},
    "z0bug.payment_4_1": {},
    "z0bug.payment_4_9": {},
    "z0bug.payment_5_9": {},
}
TEST_RES_PARTNER = {
    "z0bug.res_partner_1": {
        "name": "Prima Alpha S.p.A.",
        "street": "Via I Maggio, 101",
        "country_id": "base.it",
        "zip": "20022",
        "city": "Castano Primo",
        "state_id": "base.state_it_mi",
        "customer": True,
        "supplier": True,
        "is_company": True,
    },
    "z0bug.res_partner_2": {
        "name": "Latte Beta Due s.n.c.",
        "street": "Via Dueville, 2",
        "country_id": "base.it",
        "zip": "10060",
        "city": "S. Secondo Pinerolo",
        "state_id": "base.state_it_to",
        "customer": True,
        "supplier": False,
        "is_company": True,
    },
}
TEST_RES_PARTNER_BANK = {
    "z0bug.bank_company_1": {
        "acc_number": "IT15A0123412345100000123456",
        "partner_id": "base.main_partner",
        "acc_type": "iban",
    },
    "z0bug.bank_partner_1": {
        "acc_number": "IT73C0102001011010101987654",
        "partner_id": "z0bug.res_partner_1",
        "acc_type": "iban",
    },
    "z0bug.bank_partner_2": {
        "acc_number": "IT82B0200802002200000000022",
        "partner_id": "z0bug.res_partner_2",
        "acc_type": "iban",
    },
}
TEST_SETUP_LIST = [
    # "account.payment.term",
    # "account.payment.term.line",
    "res.partner",
    "res.partner.bank",
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super(MyTest, self).setUp()
        self.iso_code = "it_IT"

    def tearDown(self):
        super(MyTest, self).tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):
            # Save test environment, so it is available to use
            self.env.cr.commit()  # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def _test_00(self):
        # ===[Initial tests]===
        self.assertTrue(isinstance(self.setup_data_list, dict))
        self.assertTrue(isinstance(self.setup_data, dict))
        self.assertTrue(isinstance(self.struct, dict))

    def _test_01(self):
        # ===[Test declare_resource_data() function]===
        self.declare_resource_data(
            "res.partner",
            {
                "z0bug.res_partner_1": {
                    "name": "Prima Alpha S.p.A.",
                    "color": 1,
                },
            }
        )
        self.assertEqual(
            self.get_resource_list(),
            ["res.partner"]
        )
        self.assertEqual(
            self.get_resource_data_list("res.partner"),
            ["z0bug.res_partner_1"]
        )
        self.assertTrue(
            self.get_resource_data("res.partner", "z0bug.res_partner_1"),
        )
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["name"],
            "Prima Alpha S.p.A."
        )
        self.assertFalse(
            "zip" in self.get_resource_data("res.partner", "z0bug.res_partner_1"),
        )
        self.declare_resource_data(
            "res.partner",
            {
                "z0bug.res_partner_1": {
                    "name": "PRIMA ALPHA",
                    "customer": "0",
                    "supplier": "False",
                    "color": "2",
                },
            },
            merge="zerobug"
        )
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["name"],
            "PRIMA ALPHA"
        )
        # Data from public PYPI package
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["zip"],
            "20022"
        )
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["city"],
            "Castano Primo"
        )
        self.assertFalse(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["customer"],
        )
        self.assertFalse(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["supplier"],
        )

    def _test_02(self):
        # ===[Test declare_resource_data() + compute_date() functions]===
        rate_date = self.compute_date("####-12-30")
        xref = "base.EUR_%s" % rate_date
        self.declare_resource_data(
            "res.currency.rate",
            {
                xref: {
                    "currency_id": "base.EUR",
                    "name": rate_date,
                    "rate": 0.9,
                    "company_id": ""
                },
            }
        )
        self.assertEqual(
            self.get_resource_data("res.currency.rate", xref)["rate"],
            0.9
        )
        prior_date = rate_date
        rate_date = self.compute_date("+1", refdate=rate_date)
        xref = "base.EUR_%s" % rate_date
        self.declare_resource_data(
            "res.currency.rate",
            {
                xref: {
                    "currency_id": "base.EUR",
                    "name": ["+1", prior_date],
                    "rate": "0.95",
                    "company_id": ""
                },
            }
        )
        self.assertEqual(
            self.get_resource_data("res.currency.rate", xref)["rate"],
            0.95
        )

    def _test_03(self):
        # ===[Test child records + conversion data]===
        model = "res.currency"
        # The resource_write activates the child record of res.currency.rate
        self.resource_write(model, "base.EUR", {"active": True})
        self.assertTrue(self.resource_bind("base.EUR").active)
        model = "res.currency.rate"
        rate_date = self.compute_date("####-12-30")
        xref = "base.EUR_%s" % rate_date
        self.assertEqual(
            self.resource_bind(xref, resource=model).rate,
            0.9
        )
        rate_date = self.compute_date("+1", refdate=rate_date)
        xref = "base.EUR_%s" % rate_date
        self.assertEqual(
            self.resource_bind(xref, resource=model).rate,
            0.95
        )
        rate_date = self.compute_date("+1", refdate=rate_date)
        xref = "external.EUR_%s" % rate_date
        self.resource_make(model,
                           xref,
                           {
                               "currency_id": "base.EUR",
                               "name": rate_date,
                               "rate": "0.88",
                               "company_id": ""
                           })
        record = self.resource_bind(xref, resource=model)
        self.assertTrue(record)
        self.assertEqual(record.rate, 0.88)

    def _test_04(self):
        # ===[test declare_all_data() + setup_env() functions]===
        data = {"TEST_SETUP_LIST": TEST_SETUP_LIST}
        for resource in TEST_SETUP_LIST:
            item = "TEST_%s" % resource.upper().replace(".", "_")
            data[item] = globals()[item]
        self.declare_all_data(data, merge="zerobug")
        self.assertEqual(
            self.get_resource_data("res.partner.bank",
                                   "z0bug.bank_company_1")["acc_number"],
            "IT15A0123412345100000123456"
        )
        self.setup_env()
        self.assertEqual(
            self.resource_bind("z0bug.bank_company_1").acc_number,
            "IT15A0123412345100000123456"
        )

    def _test_05(self):
        # ===[test *many values]===
        model = "res.currency"
        rate_date = self.compute_date("####-12-30")
        xref = "base.EUR_%s" % rate_date
        rate_date2 = self.compute_date("+1", refdate=rate_date)
        xref2 = "base.EUR_%s" % rate_date2
        # *xmany as Odoo convention
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids":
                                    [(6, 0, [
                                        self.resource_bind(
                                            xref, resource="res.currency.rate").id,
                                        self.resource_bind(
                                            xref2, resource="res.currency.rate").id,
                                    ])]
                            })
        # *xmany as simple list
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids":
                                    [
                                        self.resource_bind(
                                            xref, resource="res.currency.rate").id,
                                        self.resource_bind(
                                            xref2, resource="res.currency.rate").id,
                                    ]
                            })
        # *xmany as simple list of text
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": [xref, xref2]
                            })
        # *2many as list in text value
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": "%s,%s" % (xref, xref2)
                            })

        # *2many as text value
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": xref
                            })
        # *xmany as integer
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": self.resource_bind(
                                    xref, resource="res.currency.rate").id
                            })

    def _test_wizard(self):
        # We engage language translation wizard with "it_IT" language
        # see "<ODOO_PATH>/addons/base/module/wizard/base_language_install*"
        _logger.info("🎺 Testing wizard.lang_install()")
        act_windows = self.wizard(
            module="base",
            action_name="action_view_base_language_install",
            default={
                "lang": self.iso_code,
                "overwrite": False,
            },
            button_name="lang_install",
        )
        self.assertTrue(
            self.is_action(act_windows),
            "No action returned by language install"
        )
        # Now we test the close message
        self.wizard(
            act_windows=act_windows
        )
        self.assertTrue(
            self.env["res.lang"].search([("code", "=", self.iso_code)]),
            "No language %s loaded!" % self.iso_code
        )

    def test_mytest(self):
        self._test_00()
        self._test_01()
        self._test_02()
        self._test_03()
        self._test_04()
        self._test_05()
        self._test_wizard()
