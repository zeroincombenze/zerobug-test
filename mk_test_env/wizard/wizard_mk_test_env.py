# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
#
from past.builtins import basestring
from builtins import int
# import os

from z0bug_odoo import z0bug_odoo_lib

from os0 import os0

from openerp.osv import fields, orm
from openerp.exceptions import Warning as UserError
try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''


class WizardMakeTestEnvironment(orm.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"

    MODULES_COA = {
        'l10n_it': ['l10n_it', 'date_range'],
        'zero': ['l10n_it_fiscal', 'date_range'],
        'axilor': ['l10n_it_fiscal', 'l10n_it_coa_base', 'date_range']
    }
    errors = []

    def _test_company(self, cr, uid, context=None):
        ids = self.pool['ir.model.data'].search(
            cr, uid,
            [('module', '=', 'z0bug'),
             ('name', '=', 'mycompany')])
        if ids:
            return self.pool['ir.model.data'].browse(cr, uid, ids[0]).res_id
        return False

    def _new_company(self, cr, uid, context=None):
        return not bool(self._test_company(cr, uid))

    def _default_company(self, cr, uid, context=None):
        return self._test_company(cr, uid) or self.pool['res.users'].browse(
            cr, uid, uid, context).company_id.id

    _columns = {
        'test_company_id': fields.many2one(
            'res.company',
            string='Test Company',
            read_only=True),
        'force_test_values': fields.boolean('Force reload test values'),
        'new_company': fields.boolean('Create new company'),
        'company_id': fields.many2one('res.company',
            string='Company',
            required=True),
        'coa': fields.selection(
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
                 '"Test" is internal testing CoA'
        ),
        'set_seq': fields.boolean('Set line sequence'),
        'load_coa': fields.boolean('Load chart of account'),
        'load_partner': fields.boolean('Load partners'),
        'load_product': fields.boolean('Load products'),
        'load_image': fields.boolean('Load record images'),
        'load_sale_order': fields.boolean('Load sale orders'),
        'load_purchase_order': fields.boolean('Load purchase orders'),
        'load_invoice': fields.boolean('Load invoices'),
        'ctr_rec_new': fields.integer('New record inserted', readonly=True),
        'ctr_rec_upd': fields.integer('Record updated', readonly=True),
        'ctr_rec_del': fields.integer('Record deleted', readonly=True),
        'status_mesg': fields.char('Installation status', readonly=True),
    }
    _defaults = {
        'test_company_id': _test_company,
        'new_company': _new_company,
        'company_id': _default_company,
        'coa': 'test',
    }
    def env_ref(self, xref, retxref_id=None):
        # We do not use standard self.pool.ref() because we need False value
        # if xref does not exits instead of exception
        # and we need to get id or record by parameter
        xrefs = xref.split('.')
        if len(xrefs) == 2:
            model = self.pool['ir.model.data']
            ids = model.search(self._cr, self._uid,
                [('module', '=', xrefs[0]), ('name', '=', xrefs[1])])
            if ids:
                rec = model.browse(self._cr, self._uid, ids[0])
                if retxref_id:
                    return rec.id
                return rec.res_id
        return False

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
        model_model = self.pool['ir.model.data']
        id = self.env_ref(xref, retxref_id=True)
        if not id:
            self.wiz.ctr_rec_new += 1
            return model_model.create(self._cr, self._uid, vals)
        model_model.write(self._cr, self._uid, id, vals)
        self.wiz.ctr_rec_upd += 1
        return id

    def add_modules(self, DICT, selector, module_list):
        if selector in DICT:
            modules = DICT[selector]
            if isinstance(modules, (list, tuple)):
                return module_list + modules
            module_list.append(modules)
        return module_list

    def install_modules(self, modules_to_install):
        modules_model = self.pool['ir.module.module']
        to_install_modules = modules_model.search(
            self._cr, self._uid,
            [('name', 'in', modules_to_install),
             ('state', '=', 'uninstalled')])
        if to_install_modules:
            modules_model.button_immediate_install(
                self._cr, self._uid, to_install_modules)
        to_install_modules = modules_model.search(
            self._cr, self._uid,
            [('name', 'in', modules_to_install),
             ('state', '=', 'uninstalled')])
        if to_install_modules:
            raise UserError(
                'Module %s not installed!' % [
                    x.id for x in modules_model.browse(
                        self._cr, self._uid, to_install_modules)])
        return

    def get_domain_field(self, model, vals, company_id,
                         field=None, parent_id=None, parent_name=None):
        for nm in ('code', 'acc_number', 'login', 'description', 'origin',
                   'sequence', 'name'):
            if nm == 'code' and model == 'product.product':
                continue
            if nm in vals and nm in self.pool[
                    'ir.model.cache'].get_struct_attr(model):
                break
        domain = [(nm, '=', vals[field or nm])]
        if 'company_id' in self.pool['ir.model.cache'].get_struct_attr(model):
            domain.append(('company_id', '=', company_id))
        if parent_id and parent_name in self.pool[
                'ir.model.cache'].get_struct_attr(model):
            domain.append((parent_name, '=', parent_id))
        ids = self.pool[model].search(
            self._cr, self._uid, domain, context={'lang': 'en_US'})
        if len(ids) == 1:
            return ids[0]
        return False

    def drop_unchanged_fields(self, vals, model, xid):
        rec = None
        if model and xid:
            rec = self.pool[model].browse(self._cr, self._uid, xid)
        for field in vals.copy():
            attrs = self.pool['ir.model.cache'].get_struct_model_attr(model,
                field)
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

    def write_diff(self, model, xid, vals):
        vals = self.drop_unchanged_fields(vals, model, xid)
        if vals:
            if 'id' in vals:
                del vals['id']
            self.pool[model].write(self._cr, self._uid, xid, vals)
            self.wiz.ctr_rec_upd += 1

    def store_xref(self, xref, model, company_id,
                   parent_id=None, parent_model=None, seq=None):
        if parent_id and parent_model:
            xid = False
        else:
            xid = self.env_ref(xref)
        if not xid or self.wiz.force_test_values:
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
            if seq:
                vals['sequence'] = seq
            vals, parent_name = self.pool['ir.model.cache'].bind_fields(
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
                    xid = self.pool[model].create(self._cr, self._uid, vals)
                    self.wiz.ctr_rec_new += 1
                if not parent_id or not parent_model:
                    self.add_xref(xref, model, xid)
        return xid

    def make_model(self, company_id, model, mode=None, model2=None):
        self.pool['ir.model.cache'].open(model=model)
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            self.store_xref(xref, model, company_id)

    def mk_account_tax(self, company_id):
        self.make_model(company_id, 'account.tax')

    def make_test_environment(self, cr, uid, ids, context=None):
        self.pool['ir.model.cache'].open(cr, uid)
        self.wiz = self.browse(cr, uid, ids[0], context=context)
        self._cr = cr
        self._uid = uid
        self.wiz.ctr_rec_new = 0
        self.wiz.ctr_rec_upd = 0
        self.wiz.ctr_rec_del = 0
        modules_to_install = []
        if self.wiz.new_company:
            modules_to_install = self.add_modules(cr, uid,
                self.MODULES_COA, self.wiz.coa, modules_to_install)
            self._create_company(cr, uid)
        self.install_modules(modules_to_install)
        if self.wiz.load_coa and self.wiz.coa == 'test':
            # self.mk_account_account(self.wiz.company_id.id)
            self.mk_account_tax(self.wiz.company_id.id)
        return {
            'name': "Data created",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.make.test.environment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'target': 'new',
            'context': {'active_id': ids[0]},
            'view_id': self.pool.get('ir.model.data').get_object_reference(
                cr, uid, 'mk_test_env', 'result_mk_test_env_view')[1],
            'domain': [('id', '=', ids[0])],
        }

    def close_window(self, cr, uid, ids, context=None):
        return
