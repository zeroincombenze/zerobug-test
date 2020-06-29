# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future import standard_library
standard_library.install_aliases()                                 # noqa: E402
from builtins import *                                             # noqa: F403
from past.builtins import basestring
from builtins import int
# import os
from datetime import date, datetime, timedelta

from z0bug_odoo import z0bug_odoo_lib

from os0 import os0

from odoo import fields
from odoo.exceptions import Warning as UserError as UserError
try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''


class WizardMakeTestEnvironment(models.TransientModel):





    def mk_account_account(self, company_id):
        model = 'account.account'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            # Prima i mastri
            if len(xref) == 12:
                self.store_xref(cr, uid,xref, model, company_id)
        for xref in xrefs:
            # poi i capoconti
            if len(xref) == 13:
                self.store_xref(cr, uid,xref, model, company_id)
        for xref in xrefs:
            # infine i sottoconti
            if len(xref) > 13:
                self.store_xref(cr, uid,xref, model, company_id)

    def mk_fiscal_position(self, company_id):
        self.make_model(company_id, 'account.fiscal.position')

    def mk_journal(self, company_id):
        self.make_model(company_id, 'account.journal')

    def mk_date_range(self, company_id):
        self.make_model(company_id, 'date.range.type')
        self.make_model(company_id, 'date.range')

    def mk_payment(self, company_id):
        model = 'account.payment.term'
        model2 = 'account.payment.term.line'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
        parent_id = False
        for xref in sorted(xrefs):
            if len(xref) == 15:
                parent_id = self.store_xref(cr, uid,xref, model, company_id)
                seq = 10
                model_model = self.env['account.payment.term.line']
                for payment_line in model_model.search(
                        [('payment_id', '=', parent_id)],
                        order='sequence,id'):
                    payment_line.write({'sequence': seq})
                    seq += 10
            else:
                self.store_xref(cr, uid,xref, model2, company_id,
                                parent_id=parent_id, parent_model=model)

    def mk_partner(self, company_id):
        model = 'res.partner'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        parent_id = False
        for xref in sorted(xrefs):
            if len(xref) <= 20 or xref == 'z0bug.partner_mycompany':
                parent_id = self.store_xref(cr, uid,xref, model, company_id)
            else:
                self.store_xref(cr, uid,xref, model, company_id, parent_id=parent_id)

    def mk_partner_bank(self, company_id):
        self.make_model(company_id, 'res.partner.bank')

    def mk_product(self, company_id):
        model = 'product.template'
        model2 = 'product.product'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            self.store_xref(cr, uid,xref, model, company_id)
            xref2 = xref.replace('z0bug.product_template',
                                 'z0bug.product_product')
            self.store_xref(cr, uid,xref2, model2, company_id)

    def mk_account_invoice(self, company_id):

        def compute_tax(inv_id):
            self.env['account.invoice'].browse(inv_id).compute_taxes()

        model = 'account.invoice'
        model2 = 'account.invoice.line'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
        parent_id = False
        for xref in sorted(xrefs):
            if len(xref) <= 19:
                if parent_id:
                    compute_tax(parent_id)
                parent_id = self.store_xref(cr, uid,xref, model, company_id)
            else:
                self.store_xref(cr, uid,xref, model2, company_id,
                                parent_id=parent_id, parent_model=model)
        if parent_id:
            compute_tax(parent_id)

    def mk_sale_order(self, company_id):

        def compute_tax(inv_id):
            return

        model = 'sale.order'
        model2 = 'sale.order.line'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
        parent_id = False
        seq = 0
        for xref in sorted(xrefs):
            if len(xref) <= 22:
                if parent_id:
                    compute_tax(parent_id)
                seq = 0
                parent_id = self.store_xref(cr, uid,xref, model, company_id)
            else:
                if self.set_seq:
                    seq += 10
                else:
                    seq = 10
                self.store_xref(cr, uid,xref, model2, company_id,
                                parent_id=parent_id, parent_model=model,
                                seq=seq)
        if parent_id:
            compute_tax(parent_id)

    def mk_purchase_order(self, company_id):

        def compute_tax(inv_id):
            return

        model = 'purchase.order'
        model2 = 'purchase.order.line'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
        parent_id = False
        parent_id_len = 0
        for xref in sorted(xrefs):
            if (not parent_id_len or
                    len(xref) <= parent_id_len):
                if not parent_id_len:
                    parent_id_len = len(xref) + 1
                if parent_id:
                    compute_tax(parent_id)
                parent_id = self.store_xref(cr, uid,xref, model, company_id)
            else:
                self.store_xref(cr, uid,xref, model2, company_id,
                                parent_id=parent_id, parent_model=model)
        if parent_id:
            compute_tax(parent_id)

    def create_company(self, cr, uid):
        vals = {
            'name': 'Test Company',
        }
        company_id = self.env['res.company'].create(vals)
        self.ctr_rec_new += 1
        self.add_xref('z0bug.mycompany', 'res.company', company_id)
        self.add_xref(
            'z0bug.partner_mycompany', 'res.partner',
            self.env['res.company'].browse(company_id).partner_id.id)

    def make_test_environment(self):
        if self.load_coa:
            self.mk_fiscal_position(self.company_id.id)
            self.mk_date_range(self.company_id.id)
            self.mk_payment(self.company_id.id)
        if self.load_partner:
            self.mk_partner(self.company_id.id)
            self.mk_partner_bank(self.company_id.id)
            self.mk_journal(self.company_id.id)
        if self.load_product:
            self.mk_product(self.company_id.id)
        if self.load_sale_order:
            self.mk_sale_order(self.company_id.id)
        if self.load_purchase_order:
            self.mk_purchase_order(self.company_id.id)
        if self.load_invoice:
            self.mk_account_invoice(self.company_id.id)
        self.status_mesg = 'Data (re)loaded'
        return {
            'name': "Data created",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.make.test.environment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'active_id': self.id},
            'view_id': self.env.ref(
                'mk_test_env.result_mk_test_env_view').id,
            'domain': [('id', '=', self.id)],
        }

    def close_window(self):
        return

