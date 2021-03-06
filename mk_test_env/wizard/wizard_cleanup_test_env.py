# -*- coding: utf-8 -*-
#
# Copyright 2019-21 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# import os
# from datetime import date, datetime, timedelta
from z0bug_odoo import z0bug_odoo_lib
# from os0 import os0

from odoo import api, fields, models
# from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''


class WizardCleanupTestEnvironment(models.TransientModel):
    _name = "wizard.cleanup.test.environment"
    _description = "Clean-up Test Environment"

    def _test_company(self):
        recs = self.env['ir.model.data'].search(
            [('module', '=', 'z0bug'),
             ('name', '=', 'mycompany')])
        if recs:
            return recs[0].res_id
        return False

    test_company_id = fields.Many2one(
        'res.company',
        string='Test Company',
        read_only=True,
        default=_test_company)
    clean_coa = fields.Boolean('Clean Chart of Account')
    clean_fiscalpos = fields.Boolean('Clean Fiscal Position')
    clean_invoice = fields.Boolean('Clean Account Invoice')
    ctr_rec_new = fields.Integer('New record inserted', readonly=True)
    ctr_rec_upd = fields.Integer('Record updated', readonly=True)
    ctr_rec_del = fields.Integer('Record deleted', readonly=True)
    status_mesg = fields.Char('Installation status',
                              readonly=True)

    @api.model
    def env_ref(self, xref, retxref_id=None):
        # We do not use standard self.env.ref() because we need False value
        # if xref does not exits instead of exception
        # and we need to get id or record by parameter
        xrefs = xref.split('.')
        if len(xrefs) == 2:
            model = self.env['ir.model.data']
            recs = model.search([('module', '=', xrefs[0]),
                                ('name', '=', xrefs[1])])
            if recs:
                if retxref_id:
                    return recs[0].id
                return recs[0].res_id
        return False

    @api.model
    def rm_ref(self, xref):
        model = self.env['ir.model.data']
        rec_id = self.env_ref(xref)
        if rec_id and model.search([('id', '=', rec_id)]):
            try:
                model.browse(rec_id).unlink()
                self.ctr_rec_del += 1
            except BaseException:
                pass

    @api.model
    def drop_xref(self, xref, model, action=None, childs=None):
        def do_action(model_model, action, rec_id):
            if not isinstance(action, (list, tuple)):
                action = [action]
            for act in action:
                if act == 'move_name=':
                    model_model.browse(rec_id).write({'move_name': ''})
                else:
                    try:
                        getattr(model_model.browse(rec_id), act)()
                    except BaseException:
                        self.env.cr.rollback()  # pylint: disable=invalid-commit

        def do_childs(model_model, childs, rec_id):
            for rec in model_model.browse(rec_id)[childs]:
                try:
                    rec.unlink()
                    self.ctr_rec_del += 1
                except BaseException:
                    self.env.cr.rollback()     # pylint: disable=invalid-commit

        model_model = self.env[model]
        rec_id = self.env_ref(xref)
        if rec_id and model_model.search([('id', '=', rec_id)]):
            if action:
                do_action(model_model, action, rec_id)
            if childs:
                do_childs(model_model, childs, rec_id)
            try:
                model_model.browse(rec_id).unlink()
                self.ctr_rec_del += 1
            except BaseException:
                self.env.cr.rollback()         # pylint: disable=invalid-commit
        self.rm_ref(xref)
        self.env.cr.commit()                   # pylint: disable=invalid-commit


    @api.model
    def clean_model(self, model, action=None):
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            self.drop_xref(xref, model, action=action)

    @api.model
    def do_clean_account_account(self):
        model = 'account.account'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs.sort()
        for xref in xrefs:
            # Prima i sottoconti
            if len(xref) > 9:
                self.drop_xref(xref, model)
        for xref in xrefs:
            # poi i capoconti
            if len(xref) == 9:
                self.drop_xref(xref, model)
        for xref in xrefs:
            # Infine i mastri
            if len(xref) == 8:
                self.drop_xref(xref, model)

    @api.model
    def do_clean_account_tax(self):
        model = 'account.tax'
        self.clean_model(model, action=None)

    @api.model
    def do_clean_fiscalpos(self):
        model = 'account.fiscal.position'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        xrefs.sort()
        for xref in xrefs:
            self.drop_xref(xref, model)

    @api.model
    def do_clean_account_invoice(self):
        model = 'account.invoice'
        self.clean_model(model, action=['move_name=', 'action_invoice_cancel'])

    def cleanup_test_environment(self):
        self.ctr_rec_new = 0
        self.ctr_rec_upd = 0
        self.ctr_rec_del = 0
        if self.test_company_id:
            if self.clean_coa:
                self.do_clean_account_account()
                self.do_clean_account_tax()
            if self.clean_fiscalpos:
                self.do_clean_fiscalpos()
            if self.clean_invoice:
                self.do_clean_account_invoice()
        return {
            'name': "Data clean-up",
            'res_model': 'wizard.cleanup.test.environment',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'view_id': self.env.ref(
                'mk_test_env.result_cleanup_test_env_view').id,
        }

    def close_window(self):
        return
