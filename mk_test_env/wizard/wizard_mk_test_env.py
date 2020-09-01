# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from past.builtins import basestring
from builtins import int
# import os
from datetime import date, datetime, timedelta
import time

from z0bug_odoo import z0bug_odoo_lib

from os0 import os0

from odoo import api, fields, models
from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''


class WizardMakeTestEnvironment(models.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"

    MODULES_COA = {
        'test': ['date_range'],
        'l10n_it': ['l10n_it', 'date_range'],
        'zero': ['l10n_it_fiscal', 'date_range'],
        'axilor': ['l10n_it_coa_base', 'date_range']
    }
    errors = []
    STRUCT = {}

    def _test_company(self):
        recs = self.env['ir.model.data'].search(
            [('module', '=', 'z0bug'),
             ('name', '=', 'mycompany')])
        if recs:
            return recs[0].res_id
        return False

    def _new_company(self):
        return not bool(self._test_company())

    def _default_company(self):
        return self._test_company() or self.env.user.company_id.id

    test_company_id = fields.Many2one(
        'res.company',
        string='Test Company',
        read_only=True,
        default=_test_company)
    force_test_values = fields.Boolean('Force reload test values')
    new_company = fields.Boolean('Create new company',
                                 default=_new_company)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=True,
                                 default=_default_company)
    coa = fields.Selection(
        [('none', 'No chart of account'),
         ('l10n_it', 'Default Odoo CoA'),
         ('zero', 'Zeroincombenze CoA'),
         ('axilor', 'Experimental Axilor CoA'),
         ('test', 'Test Chart od Account')],
        'Chart of Account',
        help='Select Chart od Account to install, if new company\n'
             '"Default Odoo Chart Account" (module l10n_it) is minimal\n'
             '"Zeroincombenze CoA" (module l10n_it_fiscal) is a full CoA\n'
             '"Axilor CoA" is a Zeroincombenze CoA plus multilevel accounts\n'
             '"Test" is internal testing CoA',
        default='test')
    set_seq = fields.Boolean('Set line sequence')
    load_coa = fields.Boolean('Load chart of account')
    load_partner = fields.Boolean('Load partners')
    load_product = fields.Boolean('Load products')
    load_image = fields.Boolean('Load record images')
    load_sale_order = fields.Boolean('Load sale orders')
    load_purchase_order = fields.Boolean('Load purchase orders')
    load_invoice = fields.Boolean('Load invoices')
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
        if (xref == 'product.product_uom_unit' and
                int(release.major_version.split('.')[0]) >= 12):
            xref = 'uom.product_uom_unit'
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
    def add_xref(self, xref, model, res_id):
        xrefs = xref.split('.')
        if len(xrefs) != 2:
            raise UserError(
                'Invalid xref %s' % xref)
        vals = {
            'module': xrefs[0],
            'name': xrefs[1],
            'model': model,
            'res_id': res_id
        }
        model_model = self.env['ir.model.data']
        id = self.env_ref(xref, retxref_id=True)
        if not id:
            self.ctr_rec_new += 1
            return model_model.create(vals)
        model_model.browse(id).model_model.write(vals)
        self.ctr_rec_upd += 1
        return id

    @api.model
    def add_modules(self, DICT, selector, module_list):
        if selector in DICT:
            modules = DICT[selector]
            if isinstance(modules, (list, tuple)):
                return module_list + modules
            module_list.append(modules)
        return module_list

    @api.model
    def install_modules(self, modules_to_install):
        modules_model = self.env['ir.module.module']
        to_install_modules = modules_model
        for module in modules_to_install:
            module_ids = modules_model.search([('name', '=', module)])
            if module_ids and module_ids[0].state == 'uninstalled':
                to_install_modules += module_ids[0]
                self.status_mesg += 'Module %s installed\n' % module
        if to_install_modules:
            to_install_modules.button_immediate_install()
            time.sleep(4)
        for module in modules_to_install:
            module_ids = modules_model.search([('name', '=', module)])
            if not module_ids or module_ids[0].state != 'installed':
                raise UserError(
                    'Module %s not installed!' % module)
        return

    def setup_model_structure(self, model):
        """Store model structure into memory"""
        if not model:
            return
        if model in self.STRUCT:
            return
        self.STRUCT[model] = self.STRUCT.get(model, {})
        for field in self.env['ir.model.fields'].search(
                [('model', '=', model)]):
            attrs = {}
            for attr in ('required', 'readonly'):
                attrs[attr] = field[attr]
            if attrs['required']:
                attrs['readonly'] = False
            if (field.ttype in ('binary', 'reference') or
                    (hasattr(field, 'related') and field.related and
                     not field.required)):
                attrs['readonly'] = True
            attrs['ttype'] = field.ttype
            attrs['relation'] = field.relation
            self.STRUCT[model][field.name] = attrs

    def get_domain_field(self, model, vals, company_id,
                         field=None, parent_id=None, parent_name=None):
        for nm in ('code', 'acc_number', 'login', 'description', 'origin',
                   'sequence', 'name'):
            if nm == 'code' and model == 'product.product':
                continue
            if nm in vals and nm in self.STRUCT[model]:
                break
        domain = [(nm, '=', vals[field or nm])]
        if 'company_id' in self.STRUCT[model]:
            domain.append(('company_id', '=', company_id))
        if parent_id and parent_name in self.STRUCT[model]:
            domain.append((parent_name, '=', parent_id))
        recs = self.env[model].with_context({'lang': 'en_US'}).search(domain)
        if len(recs) == 1:
            return recs[0].id
        return False

    @api.model
    def bind_fields(self, model, vals, company_id,
                    parent_id=None, parent_model=None):
        self.setup_model_structure(model)
        model_model = self.env[model]
        parent_name = ''
        for field in vals.copy():
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                if (model == 'account.payment.term.line' and
                        field == 'months' and
                        vals[field]):
                    vals['days'] = (int(vals[field]) * 30) - 2
                del vals[field]
                continue
            if (model == 'account.account' and
                    field == 'id' and
                    vals[field].startswith('z0bug.')):
                xrefs = vals[field].split('.')
                vals[field] = self.env_ref(vals[field])
                if not vals[field]:
                    tok = '_%s' % xrefs[1]
                    recs = self.env['ir.model.data'].search(
                        [('module', '=', 'l10n_it_fiscal'),
                         ('name', 'like', r'_\%s' % tok),
                         ('model', '=', 'account.account')])
                    for xref in recs:
                        if xref.name.endswith(tok):
                            acc = model_model.browse(xref.res_id)
                            if acc.company_id.id == company_id:
                                vals[field] = acc.id
                                break
                if 'user_type_id' in vals:
                    if self.STRUCT[model].get('nature', {}):
                        if isinstance(vals['user_type_id'], int):
                            acc = self.env['account.account.type'].browse(
                                vals['user_type_id'])
                        else:
                            acc = self.env['account.account.type'].browse(
                                self.env_ref(vals['user_type_id']))
                        if acc.nature:
                            vals['nature'] = acc.nature
                continue
            elif model == 'account.payment.term.line' and field == 'option':
                if (vals[field] == 'fix_day_following_month' and
                        int(release.major_version.split('.')[0]) >= 12):
                    vals[field] = 'day_following_month'
            elif field == 'id':
                continue
            elif parent_id and attrs.get('relation') == parent_model:
                vals[field] = parent_id
                parent_name = field
            elif field == 'company_id':
                vals[field] = company_id
                continue
            elif (attrs['ttype'] in (
                    'many2one', 'one2many', 'many2many') and
                  len(vals[field].split('.')) == 2):
                if attrs['ttype'] == 'many2one':
                    vals[field] = self.env_ref(vals[field])
                else:
                    vals[field] = [(6, 0, [self.env_ref(vals[field])])]
                continue
            elif attrs['ttype'] == 'boolean':
                vals[field] = os0.str2bool(vals[field], False)
            elif attrs['ttype'] == 'date':
                if vals[field].startswith('+'):
                    vals[field] = str(
                        date.today() + timedelta(int(vals[field][1:])))
                elif vals[field].startswith('-'):
                    vals[field] = str(
                        date.today() - timedelta(int(vals[field][1:])))
                elif vals[field].find('<#') >= 0:
                    items = vals[field].split('-')
                    for i, item in enumerate(items):
                        if item == '<#':
                            if i == 0:
                                items[i] = date.today().year - 1
                            elif i == 1:
                                items[i] = date.today().month - 1
                            elif i == 2:
                                items[i] = date.today().day - 1
                            if item[i] == 0:
                                item[i] = 1
                    vals[field] = '%04d-%02d-%02d' % (
                        int(items[0]), int(items[1]), int(items[2]))
                elif vals[field].find('#>') >= 0:
                    items = vals[field].split('-')
                    for i, item in enumerate(items):
                        if item == '#>':
                            if i == 0:
                                items[i] = date.today().year + 1
                            elif i == 1:
                                items[i] = date.today().month + 1
                                if item[i] > 12:
                                    item[i] = 12
                            elif i == 2:
                                items[i] = date.today().day + 1
                                if item[i] > 31:
                                    item[i] = 31
                    vals[field] = '%04d-%02d-%02d' % (
                        int(items[0]), int(items[1]), int(items[2]))
                elif vals[field].find('#') >= 0:
                    items = vals[field].split('-')
                    for i, item in enumerate(items):
                        if item == '#':
                            if i == 0:
                                items[i] = date.today().year
                            elif i == 1:
                                items[i] = date.today().month
                            elif i == 2:
                                items[i] = date.today().day
                    vals[field] = '%04d-%02d-%02d' % (
                        int(items[0]), int(items[1]), int(items[2]))
            elif attrs['ttype'] == 'datetime':
                if vals[field].startswith('+'):
                    vals[field] = str(
                        datetime.today() + timedelta(int(vals[field][1:])))
                elif vals[field].startswith('-'):
                    vals[field] = str(
                        datetime.today() - timedelta(int(vals[field][1:])))
            elif attrs.get('relation'):
                self.setup_model_structure(attrs['relation'])
                value = self.get_domain_field(model, vals, company_id,
                                              field=field)
                if value:
                    vals[field] = value
                else:
                    del vals[field]
        if parent_id and parent_model:
            vals['id'] = self.get_domain_field(
                model, vals, company_id,
                parent_id=parent_id, parent_name=parent_name)
            if not vals['id']:
                del vals['id']
        if (vals.get('id') and self.load_image and
                'image' in self.STRUCT[model]):
            filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(
                vals['id'])
            if filename:
                vals['image'] = z0bug_odoo_lib.Z0bugOdoo().get_image(
                    vals['id'])
        return vals, parent_name

    def drop_unchanged_fields(self, vals, model, xid):
        rec = None
        if model and xid:
            rec = self.env[model].browse(xid)
        for field in vals.copy():
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                del vals[field]
            if rec:
                if attrs['ttype'] == 'many2one':
                    if rec[field] and vals[field] == rec[field].id:
                        del vals[field]
                elif attrs['ttype'] == 'boolean':
                    if isinstance(
                            vals[field], bool) and vals[field] == rec[field]:
                        del vals[field]
                    elif os0.str2bool(vals[field], False) == rec[field]:
                        del vals[field]
                elif (isinstance(vals[field], (basestring, int)) and
                      vals[field] == rec[field]):
                    del vals[field]
        return vals

    @api.model
    def write_diff(self, model, xid, vals):
        vals = self.drop_unchanged_fields(vals, model, xid)
        if vals:
            if 'id' in vals:
                del vals['id']
            self.env[model].browse(xid).write(vals)
            self.ctr_rec_upd += 1

    @api.model
    def store_xref(self, xref, model, company_id,
                   parent_id=None, parent_model=None, seq=None):
        if parent_id and parent_model:
            xid = False
        else:
            xid = self.env_ref(xref)
        if not xid or self.force_test_values:
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
            if seq:
                vals['sequence'] = seq
            vals, parent_name = self.bind_fields(
                model, vals, company_id,
                parent_id=parent_id, parent_model=parent_model)
            if xid:
                self.write_diff(model, xid, vals)
            else:
                if vals.get('id') and isinstance(vals['id'], int):
                    xid = vals['id']
                else:
                    xid = self.get_domain_field(model, vals, company_id,
                                                parent_id=parent_id,
                                                parent_name=parent_name)
                if xid:
                    self.write_diff(model, xid, vals)
                else:
                    if 'id' in vals:
                        del vals['id']
                    try:
                        xid = self.env[model].create(vals).id
                        self.ctr_rec_new += 1
                    except BaseException:
                        xid = False
                if xid and (not parent_id or not parent_model):
                    self.add_xref(xref, model, xid)
        return xid

    @api.model
    def make_model(self, company_id, model, mode=None, model2=None):
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            self.store_xref(xref, model, company_id)

    @api.model
    def mk_account_account(self, company_id):
        model = 'account.account'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            # Prima i mastri
            if len(xref) == 12:
                self.store_xref(xref, model, company_id)
        for xref in xrefs:
            # poi i capoconti
            if len(xref) == 13:
                self.store_xref(xref, model, company_id)
        for xref in xrefs:
            # infine i sottoconti
            if len(xref) > 13:
                self.store_xref(xref, model, company_id)

    @api.model
    def mk_account_tax(self, company_id):
        self.make_model(company_id, 'account.tax')

    @api.model
    def mk_fiscal_position(self, company_id):
        self.make_model(company_id, 'account.fiscal.position')

    @api.model
    def mk_journal(self, company_id):
        self.make_model(company_id, 'account.journal')

    @api.model
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
                parent_id = self.store_xref(xref, model, company_id)
                seq = 10
                model_model = self.env['account.payment.term.line']
                for payment_line in model_model.search(
                        [('payment_id', '=', parent_id)],
                        order='sequence,id'):
                    payment_line.write({'sequence': seq})
                    seq += 10
            else:
                self.store_xref(xref, model2, company_id,
                                parent_id=parent_id, parent_model=model)

    def mk_partner(self, company_id):
        model = 'res.partner'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        parent_id = False
        for xref in sorted(xrefs):
            if len(xref) <= 20 or xref == 'z0bug.partner_mycompany':
                parent_id = self.store_xref(xref, model, company_id)
            else:
                self.store_xref(xref, model, company_id, parent_id=parent_id)

    def mk_partner_bank(self, company_id):
        self.make_model(company_id, 'res.partner.bank')

    def mk_product(self, company_id):
        model = 'product.template'
        model2 = 'product.product'
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            self.store_xref(xref, model, company_id)
            xref2 = xref.replace('z0bug.product_template',
                                 'z0bug.product_product')
            self.store_xref(xref2, model2, company_id)

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
                parent_id = self.store_xref(xref, model, company_id)
            else:
                self.store_xref(xref, model2, company_id,
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
                parent_id = self.store_xref(xref, model, company_id)
            else:
                if self.set_seq:
                    seq += 10
                else:
                    seq = 10
                self.store_xref(xref, model2, company_id,
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
                parent_id = self.store_xref(xref, model, company_id)
            else:
                self.store_xref(xref, model2, company_id,
                                parent_id=parent_id, parent_model=model)
        if parent_id:
            compute_tax(parent_id)

    @api.model
    def create_company(self):
        vals = {
            'name': 'Test Company',
        }
        company = self.env['res.company'].create(vals)
        self.ctr_rec_new += 1
        self.set_company_to_test(company)

    @api.model
    def set_company_to_test(self, company):
        self.add_xref('z0bug.mycompany', 'res.company', company.id)
        self.add_xref(
            'z0bug.partner_mycompany', 'res.partner', company.partner_id.id)

    def make_test_environment(self):
        self.ctr_rec_new = 0
        self.ctr_rec_upd = 0
        self.ctr_rec_del = 0
        self.status_mesg = ''
        modules_to_install = self.add_modules(
            self.MODULES_COA, self.coa, [])
        if self.new_company:
            self.create_company()
        elif not self.test_company_id:
            self.set_company_to_test(self.company_id)
        self.install_modules(modules_to_install)
        if self.load_coa and self.coa == 'test':
            self.mk_account_account(self.company_id.id)
            self.mk_account_tax(self.company_id.id)
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
        self.status_mesg += 'Data (re)loaded'
        return {
            'name': "Data created",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.make.test.environment',
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
