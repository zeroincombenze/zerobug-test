# -*- coding: utf-8 -*-
from future.utils import PY2
import os
from datetime import date, datetime
import logging
import base64
from odoo.modules.module import get_module_resource
from .testenv import MainTest as SingleTransactionCase

import python_plus

_logger = logging.getLogger(__name__)


TEST_ACCOUNT_ACCOUNT = {
    "z0bug.coa_tax_recv": {
        "code": "111200",
        "reconcile": False,
        "user_type_id": "account.data_account_type_current_liabilities",
        "name": "IVA n/debito",
    },
    "z0bug.coa_sale": {
        "code": "200000",
        "name": "Merci c/vendita",
        "user_type_id": "account.data_account_type_revenue",
        "reconcile": False,
    },
    "z0bug.coa_sale2": {
        "code": "200010",
        "name": "Ricavi da servizi",
        "user_type_id": "account.data_account_type_revenue",
        "reconcile": False,
    },
}

TEST_ACCOUNT_JOURNAL = {
    "external.INV": {
        "code": "INV",
        "type": "sale",
        "update_posted": True,
        "name": "Fatture di vendita",
    },
    "external.BNK1": {
        "code": "BNK1",
        "type": "bank",
        "update_posted": True,
        "name": "Banca",
    },
}

TEST_ACCOUNT_INVOICE = {

    "z0bug.invoice_Z0_1": {
        "date_invoice": "####-<#-99",
        "journal_id": "external.INV",
        "origin": "P1/2021/0001",
        "partner_id": "z0bug.res_partner_1",
        "reference": "P1/2021/0001",
        "type": "out_invoice",
        "payment_term_id": "z0bug.payment_term_1",
    },
    "z0bug.invoice_Z0_2": {
        "date_invoice": "####-<#-99",
        "journal_id": "external.INV",
        "origin": "SO123",
        "partner_id": "z0bug.res_partner_2",
        "reference": "SO123",
        "type": "out_invoice",
        "payment_term_id": "z0bug.payment_term_2",
    },
}

TEST_ACCOUNT_INVOICE_LINE = {
    "z0bug.invoice_Z0_1_1": {
        "invoice_id": "z0bug.invoice_Z0_1",
        "account_id": "z0bug.coa_sale",
        "invoice_line_tax_ids": "external.22v",
        "name": "Prodotto Alpha",
        "price_unit": 0.84,
        "product_id": "z0bug.product_product_1",
        "quantity": 100,
        "sequence": 1,
    },
    "z0bug.invoice_Z0_1_2": {
        "invoice_id": "z0bug.invoice_Z0_1",
        "account_id": "z0bug.coa_sale2",
        "invoice_line_tax_ids": "external.22v",
        "name": "Special Worldwide service",
        "price_unit": 1.88,
        "product_id": "z0bug.product_product_23",
        "quantity": 1,
        "sequence": 2,
    },
    "z0bug.invoice_Z0_1_03": {
        "invoice_id": "z0bug.invoice_Z0_1",
        "account_id": "z0bug.coa_sale",
        "invoice_line_tax_ids": "external.22v",
        "name": "Reference line",
        "price_unit": 0.0,
        "product_id": False,
        "quantity": 1,
        "sequence": 3,
    },
    "z0bug.invoice_Z0_2_1": {
        "invoice_id": "z0bug.invoice_Z0_2",
        "account_id": "z0bug.coa_sale",
        "invoice_line_tax_ids": "external.22v",
        "name": "Prodotto Alpha",
        "price_unit": 0.84,
        "product_id": "z0bug.product_product_1",
        "quantity": 100,
        "sequence": 1,
    },
    "z0bug.invoice_Z0_2_2": {
        "invoice_id": "z0bug.invoice_Z0_2",
        "account_id": "z0bug.coa_sale",
        "invoice_line_tax_ids": "external.22v",
        "name": "Prodotto Rho",
        "price_unit": 1.69,
        "product_id": "z0bug.product_product_18",
        "quantity": 10,
        "sequence": 2,
    },
}

TEST_ACCOUNT_PAYMENT_TERM = {
    "z0bug.payment_term_1": {
        "name": "RiBA 30 GG",
    },
    "z0bug.payment_term_2": {
        "name": "RiBA 30/60 GG",
    },
}

TEST_ACCOUNT_PAYMENT_TERM_LINE = {
    "z0bug.payment_term_1_1": {
        "payment_id": "z0bug.payment_term_1",
        "sequence": 1,
        "days": 30,
        "value": "balance",
    },
    "z0bug.payment_term_2_1": {
        "payment_id": "z0bug.payment_term_2",
        "sequence": 1,
        "days": 30,
        "value": "percent",
        "value_amount": 50,
    },
    "z0bug.payment_term_2_2": {
        "payment_id": "z0bug.payment_term_2",
        "sequence": 2,
        "months": 2,
        # "days": 60,
        "value": "balance",
    },
}

TEST_ACCOUNT_TAX = {
    "external.22v": {
        "description": "22v",
        "name": "IVA 22% su vendite",
        "amount_type": "percent",
        "account_id": "z0bug.coa_tax_recv",
        "refund_account_id": "z0bug.coa_tax_recv",
        "amount": 22,
        "type_tax_use": "sale",
        "price_include": False,
    },
}

TEST_PRODUCT_TEMPLATE = {
    # Consumable product
    "z0bug.product_template_1": {
        "default_code": "AA",
        "name": "Prodotto Alpha",
        "lst_price": 0.84,
        "standard_price": 0.42,
        "categ_id": "product.product_category_1",
        "type": "consu",
        "uom_id": "product.product_uom_unit",
        "uom_po_id": "product.product_uom_unit",
        "weight": 0.1,
        "image": False,
        "property_account_income_id": "z0bug.coa_sale",
    },
    # Product on stock
    "z0bug.product_template_18": {
        "default_code": "RR",
        "name": "Prodotto Rho",
        "lst_price": 1.19,
        "standard_price": 0.59,
        "type": "product",
        "uom_id": "product.product_uom_unit",
        "uom_po_id": "product.product_uom_unit",
        "weight": 0.06,
        "image": False,
        "property_account_income_id": "z0bug.coa_sale",
    },
    # Service
    'z0bug.product_template_23': {
        'default_code': 'WW',
        'name': 'Special Worldwide service',
        'lst_price': 1.88,
        'standard_price': 0,
        'type': 'service',
        'uom_id': 'product.product_uom_unit',
        'uom_po_id': 'product.product_uom_unit',
        "image": "z0bug.product_template_26.png",
        "property_account_income_id": "z0bug.coa_sale2",
    },
}
TEST_RES_PARTNER = {
    "z0bug.partner_mycompany": {
        "name": "Test Company",
        "street": "Via dei Matti, 0",
        # "country_id": "base.it",
        "zip": "20080",
        "city": "Ozzero",
        "state_id": "base.state_it_mi",
        "customer": False,
        "supplier": False,
        "is_company": True,
        "email": "info@testcompany.org",
        "phone": "+39 025551234",
        # "vat": "IT05111810015",
        "website": "https://www.testcompany.org",
    },
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
        "image": "z0bug.res_partner_1.png",
    },
    "z0bug.res_partner_2": {
        "name": "Latte Beta Due s.n.c.",
        "street": "Via Dueville, 2",
        "country_id": "base.it",
        "zip": "10060",
        "city": "S. Secondo Parmense",
        "state_id": "base.state_it_pr",
        "customer": True,
        "supplier": False,
        "is_company": True,
        "image": "z0bug.res_partner_2",
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
    "res.partner",
    "res.partner.bank",
    "product.template",
]


class MyTest(SingleTransactionCase):

    def setUp(self):
        super(MyTest, self).setUp()
        self.debug_level = 2
        self.iso_code = "it_IT"
        self.date_rate_0 = self.compute_date("####-12-30")

    def tearDown(self):
        super(MyTest, self).tearDown()
        if os.environ.get("ODOO_COMMIT_TEST", ""):                   # pragma: no cover
            # Save test environment, so it is available to use
            self.env.cr.commit()                       # pylint: disable=invalid-commit
            _logger.info("✨ Test data committed")

    def _test_00(self):
        # ===[Preliminary tests]===
        self.assertTrue(isinstance(self.setup_data_list, dict))
        self.assertTrue(isinstance(self.setup_data, dict))
        self.assertTrue(isinstance(self.struct, dict))

    def _test_01(self):
        # ===[Test declare_resource_data() function w/o merge]===
        self.declare_resource_data(
            "res.partner",
            {
                "z0bug.res_partner_1": {
                    "name": "Prima Alpha S.p.A.",
                    "color": 1,
                    "not_exist_field": "INVALID",
                    "street": None,
                },
            }
        )
        self.assertEqual(
            self.get_resource_list(),
            ["res.partner"],
            "declare_resource_data() FAILED: 'res.partner' not found in resource list!"
        )
        self.assertEqual(
            self.get_resource_data_list("res.partner"),
            ["z0bug.res_partner_1"],
            (
                "declare_resource_data() FAILED: "
                "'z0bug.res_partner_1' xref not found in 'res.partner' data!"
            )
        )
        self.assertTrue(
            self.get_resource_data("res.partner", "z0bug.res_partner_1"),
            "get_resource_data() FAILED: no value found for 'z0bug.res_partner_1'!"
        )
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["name"],
            "Prima Alpha S.p.A.",
            "TestEnv FAILED: unexpected value for 'name'!"
        )
        self.assertFalse(
            "zip" in self.get_resource_data("res.partner", "z0bug.res_partner_1"),
            "TestEnv FAILED: unexpected field value for 'zip'!"
        )
        self.assertFalse(
            "not_exist_field" in self.get_resource_data(
                "res.partner", "z0bug.res_partner_1"),
            "TestEnv FAILED: unexpected field 'not_exist_field'!"
        )
        self.assertFalse(
            "street" in self.get_resource_data("res.partner", "z0bug.res_partner_1"),
            "TestEnv FAILED: unexpected field value for 'street'!"
        )

    def _test_02(self):
        # ===[Test declare_resource_data() function with merge]===
        # Warning! Pay attention to this test: it requires z0bug_odoo>=2.0.3<3.0.0
        self.declare_resource_data(
            "res.partner",
            {
                "z0bug.res_partner_2": TEST_RES_PARTNER["z0bug.res_partner_2"]
            },
        )
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_2")["city"],
            "S. Secondo Parmense",
            "TestEnv FAILED: unexpected value for 'city'!"
        )
        _logger.info("Please, ignore field <...> does not exist in <...>")
        self.declare_resource_data(
            "res.partner",
            {
                "z0bug.res_partner_1": {
                    "name": "PRIMA ALPHA",
                    "customer": "0",
                    "supplier": "False",
                    "color": "2",
                },
                "z0bug.res_partner_2": {},
            },
            merge="zerobug"
        )
        _logger.info("Now, all warning & messages are valid!")
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_1")["name"],
            "PRIMA ALPHA"
        )
        # Data from public PYPI package
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_2")["city"],
            "S. Secondo Pinerolo",
            "TestEnv FAILED: value for 'city' not updated by PYPI!"
        )
        # Lang of partner is 'it_IT' but it does not exist
        self.assertEqual(
            self.get_resource_data("res.partner", "z0bug.res_partner_2")["lang"],
            "it_IT"
        )
        self.resource_make("res.partner", "z0bug.res_partner_2")
        self.assertEqual(
            self.resource_bind("z0bug.res_partner_2")["lang"],
            "en_US"
        )
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

    def _test_03(self):
        # ===[Test declare_resource_data() + compute_date() functions]===
        # Warning! Pay attention to this test: it requires python_plus>=2.0.1
        rate_date = self.date_rate_0
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
        self.date_rate_1 = self.compute_date("+1", refdate=rate_date)
        xref = "base.EUR_%s" % self.date_rate_1
        self.declare_resource_data(
            "res.currency.rate",
            {
                xref: {
                    "currency_id": "base.EUR",
                    "name": ["+1", self.date_rate_0],
                    "rate": "0.95",
                    "company_id": ""
                },
            }
        )
        self.assertEqual(
            self.get_resource_data("res.currency.rate", xref)["rate"],
            0.95
        )

    def _test_04(self):
        # ===[Test child records + conversion data]===
        model = "res.currency"
        # The resource_write activates the child record of res.currency.rate
        self.resource_write(model, "base.EUR", {"active": True})
        self.assertTrue(self.resource_bind("base.EUR").active)
        model = "res.currency.rate"
        xref = "base.EUR_%s" % self.date_rate_0
        self.assertEqual(
            self.resource_bind(xref, resource=model).rate,
            0.9
        )
        xref = "base.EUR_%s" % self.date_rate_1
        self.assertEqual(
            self.resource_bind(xref, resource=model).rate,
            0.95
        )
        self.date_rate_2 = self.compute_date("+1", refdate=self.date_rate_1)
        xref = "external.EUR_%s" % self.date_rate_2
        self.resource_make(model,
                           xref,
                           {
                               "currency_id": "base.EUR",
                               "name": self.date_rate_2,
                               "rate": "0.88",
                               "company_id": ""
                           })
        record = self.resource_bind(xref, resource=model)
        self.assertTrue(record)
        self.assertEqual(record.rate, 0.88)

    def _test_setup(self):
        # ===[test declare_all_data() + setup_env() functions]===
        # This is the ordinary test way
        data = {"TEST_SETUP_LIST": TEST_SETUP_LIST}
        for resource in TEST_SETUP_LIST:
            item = "TEST_%s" % resource.upper().replace(".", "_")
            data[item] = globals()[item]
        # Add alias to company
        self.declare_all_data(data)
        self.setup_company(self.default_company(),
                           xref="z0bug.mycompany",
                           partner_xref="z0bug.partner_mycompany",
                           bnk1_xref="z0bug.coa_bnk1",
                           values={
                               "name": "Test Company",
                               "vat": "IT05111810015",
                               "country_id": "base.it",
                           })
        # In TEST_RES_PARTNER vat is not declared
        self.assertFalse(
            self.get_resource_data("res.partner",
                                   "z0bug.partner_mycompany").get("vat", ""),
        )
        self.assertEqual(
            self.get_resource_data(
                "res.partner.bank",
                "z0bug.bank_company_1")["acc_number"].replace(" ", ""),
            "IT15A0123412345100000123456"
        )
        self.setup_env()
        self.assertEqual(
            self.resource_bind("z0bug.bank_company_1").acc_number.replace(" ", ""),
            "IT15A0123412345100000123456"
        )
        self.assertEqual(
            self.default_company().country_id,
            self.env.ref("base.it")
        )
        self.assertEqual(
            self.resource_bind("z0bug.res_partner_2")["city"],
            "S. Secondo Parmense",
            "TestEnv FAILED: unexpected value for 'city'!"
        )

        # Test alias
        self.assertEqual(
            self.resource_bind("z0bug.partner_mycompany")["vat"],
            "IT05111810015"
        )
        # Vat number must be loaded by setup_company()
        self.assertEqual(
            self.resource_bind("base.main_company")["vat"],
            "IT05111810015"
        )

        data = {
            "TEST_SETUP_LIST": ["account.payment.term", "account.payment.term.line"],
            "TEST_ACCOUNT_PAYMENT_TERM": TEST_ACCOUNT_PAYMENT_TERM,
            "TEST_ACCOUNT_PAYMENT_TERM_LINE": TEST_ACCOUNT_PAYMENT_TERM_LINE,
        }
        self.declare_all_data(data, group="payment_term")
        self.setup_env(group="payment_term")
        self.assertEqual(
            self.resource_bind("z0bug.payment_term_1")["name"],
            "RiBA 30 GG"
        )

    def _test_many2one(self):
        partner = self.resource_bind("z0bug.res_partner_2")
        self.resource_write("res.partner", "z0bug.res_partner_2",
                            values={"country_id": self.env.ref("base.it").id})
        self.assertEqual(
            partner.country_id,
            self.env.ref("base.it")
        )
        self.resource_write("res.partner", "z0bug.res_partner_2",
                            values={"country_id": self.env.ref("base.it")})
        self.assertEqual(
            partner.country_id,
            self.env.ref("base.it")
        )
        self.resource_write(
            "res.partner", "z0bug.res_partner_2",
            values={"country_id": "external.%s" % self.env.ref("base.it").id})
        self.assertEqual(
            partner.country_id,
            self.env.ref("base.it")
        )

    def _test_currency_2many(self):
        # ===[test *many values]===
        # Types <one2many>
        _logger.info("🎺 Testing test_currency_2many()")
        model = "res.currency"
        xref = "base.EUR_%s" % self.date_rate_0
        xref1 = "base.EUR_%s" % self.date_rate_1
        # *xmany as Odoo convention (1)
        self.resource_write(
            model, "base.EUR",
            {
                "rate_ids":
                    [(6, 0, [
                        self.resource_bind(xref, resource="res.currency.rate").id,
                        self.resource_bind(xref1, resource="res.currency.rate").id,
                    ])]
            })
        # *xmany as Odoo convention (2)
        self.resource_write(
            model, "base.EUR",
            {
                "rate_ids":
                    [
                        (0, 0, {"name": "2022-01-01", "rate": 0.77}),
                    ]
            })
        # *xmany as Odoo convention (3)
        self.resource_write(
            model, "base.EUR",
            {
                "rate_ids":
                    [
                        (1,
                         self.resource_bind(xref, resource="res.currency.rate").id,
                         self.get_resource_data("res.currency.rate", xref)),
                        (1,
                         self.resource_bind(xref1, resource="res.currency.rate").id,
                         self.get_resource_data("res.currency.rate", xref1)),
                    ]
            })
        # *xmany as simple list
        self.resource_write(
            model, "base.EUR",
            {
                "rate_ids":
                    [
                        self.resource_bind(xref, resource="res.currency.rate").id,
                        self.resource_bind(xref1, resource="res.currency.rate").id,
                    ]
            })
        # *xmany as simple list of text
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": [xref, xref1]
                            })
        # *2many as list in text value
        self.resource_write(model, "base.EUR",
                            {
                                "rate_ids": "%s,%s" % (xref, xref1)
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
        # without *xmany field: rate_ids will be loaded internally
        self.resource_write(model, "base.EUR", {})

    def _simple_field_test(self, record, xref, field, target_value):
        record = self.resource_write(record, xref, values={field: target_value})
        ttype = record._fields[field].type
        if ttype == "many2one":
            self.assertEqual(
                record[field].id,
                int(target_value),
                "TestEnv FAILED: invalid field '%s'!" % field
            )
        else:
            self.assertEqual(
                record[field], python_plus._u(target_value),
                "TestEnv FAILED: invalid field '%s'!" % field
            )
        product = self.resource_write(record, xref)
        if ttype == "many2one":
            self.assertEqual(
                product[field].id,
                self.get_resource_data(
                    product._name, xref=xref).get(field, product[field].id),
                "TestEnv FAILED: invalid field '%s'!" % field
            )
        else:
            self.assertEqual(
                product[field],
                self.get_resource_data(
                    product._name, xref=xref).get(field, product[field]),
                "TestEnv FAILED: invalid field '%s'!" % field
            )

    def _test_product(self):
        # Product type may be 'product' just if 'stock' module is installed
        # So, type 'product' becomes 'cons'; type 'service' still keeps its own value
        _logger.info("🎺 Testing test_product()")
        self.assertEqual(
            self.resource_bind("z0bug.product_product_18").type,
            "consu",
            "TestEnv FAILED: invalid product type!"
        )
        self.assertEqual(
            self.resource_bind("z0bug.product_product_23").type,
            "service",
            "TestEnv FAILED: invalid product type!"
        )

        # *** Now we test different field type values ***
        # resource = "product.template"
        xref = "z0bug.product_product_18"
        product = self.resource_bind(xref)

        # Type <char>
        self._simple_field_test(product, xref, "default_code", "ρ")

        # Type <selection>
        self._simple_field_test(product, xref, "type", "service")

        # Type <boolean>
        self._simple_field_test(product, xref, "sale_ok", True)

        # Type <integer>
        self._simple_field_test(product, xref, "color", 7)

        # Type <float>
        self._simple_field_test(product, xref, "lst_price", 0.99)

        # Type <text>
        self._simple_field_test(
            product, xref, "description", "Product Rho (greek letter ρ)")

        # Type <many2one>
        target = self.env.ref("product.product_category_all").id
        self._simple_field_test(product, xref, "categ_id", target)
        target = str(self.env.ref("product.product_category_all").id)
        self._simple_field_test(product, xref, "categ_id", target)

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

    def _test_partner(self):
        # Repeat setup with language it_IT
        self.setup_env(lang=self.iso_code)

        # Warning! Pay attention to this test: it downloads gravatar image
        # Based on Odoo partner feature. Tested on Odoo 10.0, 12.0; it requires:
        # - image is null (2° web_change)
        # - email with gravatar (antoniomaria.vigliotti@gmail.com)
        partner = self.resource_bind("z0bug.res_partner_1")
        self.resource_edit(
            resource=partner,
            web_changes=[
                ("name", "PRIMA ALPHA S.P.A."),
                ("image", False),
                ("email", "antoniomaria.vigliotti@gmail.com"),
            ],
            ctx={"gravatar_image": True},
        )
        self.assertTrue(
            partner.image,
            "partner.onchange_email() FAILED: no gravatar image downloaded!"
        )

    def _test_invoice(self):
        data = {
            "TEST_SETUP_LIST": [
                "account.account",
                "account.tax",
                "account.journal",
                "account.invoice",
                "account.invoice.line",
            ],
            "TEST_ACCOUNT_ACCOUNT": TEST_ACCOUNT_ACCOUNT,
            "TEST_ACCOUNT_TAX": TEST_ACCOUNT_TAX,
            "TEST_ACCOUNT_JOURNAL": TEST_ACCOUNT_JOURNAL,
            "TEST_ACCOUNT_INVOICE": TEST_ACCOUNT_INVOICE,
            "TEST_ACCOUNT_INVOICE_LINE": TEST_ACCOUNT_INVOICE_LINE,
        }
        self.declare_all_data(data, group="invoice")
        self.setup_env(group="invoice")

        # Test reading record without resource declaration by <external> xref
        bnk_journal = self.resource_bind("external.BNK1")

        invoice = self.resource_bind("z0bug.invoice_Z0_2")
        self.resource_edit(
            resource=invoice,
            actions="action_invoice_open"
        )
        self.assertEqual(
            invoice.state,
            "open",
            "action_invoice_open() FAILED: no state changed!"
        )

        self.resource_edit(
            resource=invoice,
            actions="action_invoice_cancel"
        )
        self.assertEqual(
            invoice.state,
            "cancel",
            "action_invoice_cancel() FAILED: no state changed!"
        )

        self.resource_edit(
            resource=invoice,
            actions="action_invoice_draft",
        )
        self.assertEqual(
            invoice.state,
            "draft",
            "action_invoice_draft() FAILED: no state changed!"
        )
        return invoice

    def _test_wizard_invoice(self):
        invoices = self.env["account.invoice"]
        invoices |= self.resource_bind("z0bug.invoice_Z0_1")
        invoices |= self.resource_bind("z0bug.invoice_Z0_2")

        self.wizard(
            module="account",
            action_name="action_account_invoice_confirm",
            records=invoices,
            button_name="invoice_confirm"
        )
        for invoice in invoices:
            self.assertEqual(
                invoice.state,
                "open",
                "action_invoice_open() FAILED: no state changed!"
            )

        invoice = self.resource_bind("z0bug.invoice_Z0_1")
        act_windows = self.resource_edit(
            resource=invoice,
            actions="account.action_account_invoice_payment",
        )
        self.assertTrue(self.is_action(act_windows))
        self.wizard(
            act_windows=act_windows,
            default={
                "journal_id": "external.BNK1",
            },
            button_name="post",
        )
        return invoice.move_id

    def _test_move(self, move):
        self.resource_edit(
            resource=move,
            actions="button_cancel"
        )
        self.assertEqual(move.state, "draft")
        saved_ref = move.ref
        self.resource_write(move, values={"ref": "payment"})
        self.resource_write("account.move", move.id, values={"ref": saved_ref})
        self.resource_edit(
            resource=move,
            actions="post"
        )
        self.assertEqual(move.state, "posted")

    def _test_testenv_all_fields(self):
        binary_fn = get_module_resource(self.module.name, "tests", "data", "example.xml")
        with open(binary_fn, "rb") as fd:
            source_xml = fd.read()
        saved_ts = datetime.now()
        html = """<div>Example <b>Test</b></div>"""

        record = self.resource_edit(
            resource="testenv.all.fields",
            web_changes=[
                ("name", "Name"),
                ("active", False),
                ("active", True),
                ("state", "confirmed"),
                ("state", "draft"),
                ("description", "Almost long long description"),
                ("rank", 13),
                ("rank", "17"),
                ("amount", "12.3"),
                ("amount", 23.4),
                ("measure", "34.5"),
                ("measure", 45.6),
                ("date", "####-##-01"),
                ("date", date(2022, 6, 22)),
                ("date", "2022-06-26"),
                ("created_dt", "####-##-02"),
                ("created_dt", "####-##-02 10:11:12"),
                ("updated_dt", saved_ts),
                ("attachment", "example.xml"),
                ("webpage", html),
                ("partner_ids", "z0bug.res_partner_1"),
                ("partner_ids", ["z0bug.res_partner_1", "z0bug.res_partner_2"]),
                ("product_ids", ["z0bug.product_product_1",
                                 "z0bug.product_product_18",
                                 "z0bug.product_product_23"]),
            ],
        )
        self.assertEqual(record.name, "Name")
        self.assertTrue(record.active)
        self.assertEqual(record.state, "draft")
        self.assertEqual(record.description, "Almost long long description")
        self.assertEqual(record.rank, 17)
        self.assertEqual(record.amount, 23.4)
        self.assertEqual(record.measure, 45.6)
        self.assertEqual(record.date,
                         "2022-06-26" if PY2 else date(2022, 6, 26))
        res = self.compute_date("####-##-02 10:11:12")
        self.assertEqual(record.created_dt,
                         res if PY2 else datetime.strptime(res, "%Y-%m-%d %H:%M:%S"))
        self.assertEqual(record.updated_dt,
                         datetime.strftime(saved_ts, "%Y-%m-%d %H:%M:%S")
                         if PY2 else saved_ts)
        self.assertEqual(record.attachment, base64.b64encode(source_xml))
        self.assertEqual(self.field_download(record, "attachment"), source_xml)
        self.assertEqual(
            record.webpage,
            "<p>" + html.replace("<div>", "").replace("</div>", "") + "</p>")
        res = self.env["res.partner"]
        res |= self.resource_bind("z0bug.res_partner_1")
        res |= self.resource_bind("z0bug.res_partner_2")
        self.assertEqual(record.partner_ids, res)
        res = self.env["product.product"]
        res |= self.resource_bind("z0bug.product_product_1")
        res |= self.resource_bind("z0bug.product_product_18")
        res |= self.resource_bind("z0bug.product_product_23")
        self.assertEqual(record.product_ids, res)

        record = self.resource_edit(
            resource=record,
            web_changes=[
                ("description", False),
            ],
        )
        self.assertEqual(record.description, False)

    def _test_validate_record(self):
        _logger.info("🎺 Testing validate_record()")
        self.resource_write("res.partner", xref="z0bug.res_partner_1")
        self.resource_write("res.partner", xref="z0bug.res_partner_2")
        records = self.env["res.partner"]
        records |= self.resource_bind("z0bug.res_partner_1")
        records |= self.resource_bind("z0bug.res_partner_2")

        # Test with good information
        template = [
            {
                "name": TEST_RES_PARTNER["z0bug.res_partner_1"]["name"],
                "street": TEST_RES_PARTNER["z0bug.res_partner_1"]["street"],

            },
            {
                "name": TEST_RES_PARTNER["z0bug.res_partner_2"]["name"],
                "country_id": "base.it",
            },
        ]
        self.validate_records(template, records)

        # Test with weak information
        template = [
            {
                "customer": True
            },
            {
                "customer": True            },
        ]
        self.validate_records(template, records)

        # Test with header/detail record
        self.resource_write("account.payment.term", xref="z0bug.payment_term_2")
        template = [
            {
                "name": TEST_ACCOUNT_PAYMENT_TERM["z0bug.payment_term_2"]["name"],
                "line_ids": [
                    {
                        "days": TEST_ACCOUNT_PAYMENT_TERM_LINE[
                            "z0bug.payment_term_2_1"]["days"],
                        "value": TEST_ACCOUNT_PAYMENT_TERM_LINE[
                            "z0bug.payment_term_2_1"]["value"],
                        "value_amount": TEST_ACCOUNT_PAYMENT_TERM_LINE[
                            "z0bug.payment_term_2_1"]["value_amount"],
                    },
                    {
                        "days": 60,
                        "value": TEST_ACCOUNT_PAYMENT_TERM_LINE[
                            "z0bug.payment_term_2_2"]["value"],
                    },                ],
            },
        ]
        records = [self.resource_bind("z0bug.payment_term_2")]
        self.validate_records(template, records)

    def _test_wizard_from_menu(self):
        act_windows = self.wizard(
            module=".",
            action_name="wizard_example_menu_view",
            web_changes=[("numrecords", 3)],
            button_name="do_example"
        )
        self.assertTrue(self.is_action(act_windows))
        records = self.get_records_from_act_windows(act_windows)
        self.assertEqual(
            len(records),
            3,
            "Wizard did not return 3 records!"
        )
        template = [
            {
                "rank": 1
            },
            {
                "rank": 2
            },
            {
                "rank": 3
            },
        ]
        self.validate_records(template, records)

    def test_mytest(self):
        self._test_00()
        self._test_01()
        self._test_02()
        self._test_03()
        self._test_04()
        self._test_setup()
        self._test_many2one()
        self._test_currency_2many()
        self._test_testenv_all_fields()
        self._test_product()
        self._test_wizard()
        #
        self._test_partner()
        self._test_invoice()
        move = self._test_wizard_invoice()
        self._test_move(move)
        self._test_validate_record()
        self._test_wizard_from_menu()
