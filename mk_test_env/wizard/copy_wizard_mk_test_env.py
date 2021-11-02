# -*- coding: utf-8 -*-
#
# Copyright 2019-21 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
from past.builtins import basestring
from builtins import int
# import os
from datetime import date, datetime, timedelta
import time
import calendar

from openerp import api, fields, models
from openerp.exceptions import Warning as UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''

from z0bug_odoo import z0bug_odoo_lib
from os0 import os0
from clodoo import transodoo


MODULES_NEEDED = {
    '': ['calendar', 'mail', 'product', 'stock'],
    'coa': {
        'test': [],
        'l10n_it': ['l10n_it'],
        'zero': ['l10n_it_fiscal'],
        'powerp': ['l10n_it_coa_base']
    },
    'load_coa': {
        '': [],
        'coa': ['date_range',
                'account_payment_term_extension',
                'l10n_it_fiscalcode'],
        'sp': ['l10n_it_split_payment'],
        'li': ['l10n_it_lettera_intento'],
        'rc': ['l10n_it_reverse_charge'],
        'wh': ['l10n_it_withholding_tax'],
        'sct': ['account_banking_sepa_credit_transfer'],
        'sdd': ['account_banking_sepa_direct_debit'],
        'conai': ['l10n_it_conai'],
    },
    'load_product': [],
    'load_partner': ['partner_bank'],
    'load_sale_order': ['sale', 'l10n_it_ddt'],
    'load_purchase_order': ['purchase'],
    'load_invoice': ['account', 'account_accountant', 'account_cancel',
                     'payment', 'l10n_it_einvoice_in', 'l10n_it_einvoice_out'],
}
COA_MODULES = ['l10n_it', 'l10n_it_fiscal', 'l10n_it_coa_base']


class WizardMakeTestEnvironment(models.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"

    errors = []
    STRUCT = {}

    @api.model
    def _test_company(self):
        recs = self.pool['ir.model.data'].search(
            self._cr, self._uid,
            [('module', '=', 'z0bug'),
             ('name', '=', 'mycompany')])
        if recs:
            return recs[0].res_id
        return False

    @api.model
    def _new_company(self):
        return not bool(self._test_company())

    @api.model
    def _default_company(self):
        return self._test_company() or self.pool['res.users']._get_company(
            self._cr, self._uid)

    test_company_id = fields.Many2one(
        'res.company',
        string='Test Company',
        read_only=True,)
        ## default=_test_company)
    force_test_values = fields.Boolean('Force reload test values')
    new_company = fields.Boolean('Create new company',)
                                 ## default=_new_company)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=True,)
                                 ## default=_default_company)
    coa = fields.Selection(
        [('none', 'No chart of account'),
         ('l10n_it', 'Default Odoo CoA'),
         ('zero', 'Zeroincombenze CoA'),
         ('powerp', 'Experimental Powerp CoA'),
         ('test', 'Test Chart od Account')],
        'Chart of Account',
        help='Select Chart od Account to install, if new company\n'
             '"Default Odoo Chart Account" (module l10n_it) is minimal\n'
             '"Zeroincombenze CoA" (module l10n_it_fiscal) is a full CoA\n'
             '"Powero CoA" means manual CoA\n'
             '"Test" is internal testing CoA',
        default='zero')
    set_seq = fields.Boolean('Set line sequence')
    load_coa = fields.Selection(
        [('', 'Minimal'),
         ('coa', 'Load CoA'),
         ('sp', 'Split Payment'),
         ('li', 'Lettere Intento'),
         ('rc', 'Reverse Charge'),
         ('wh', 'Withholding Tax'),
         ('sct', 'Sepa Credit Transfer'),
         ('sdd', 'Sepa Direct Debit'),
         ('conai', 'Conai'),
         ], 'Load specific account')
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
    #
    # @api.model
    # def env_ref(self, xref, retxref_id=None):
    #     # We do not use standard self.env.ref() because we need False value
    #     # if xref does not exits instead of exception
    #     # and we need to get id or record by parameter
    #     if (xref == 'product.product_uom_unit' and
    #             eval(release.major_version.split('.')[0]) >= 12):
    #         xref = 'uom.product_uom_unit'
    #     xrefs = xref.split('.')
    #     if len(xrefs) == 2:
    #         model = self.pool['ir.model.data']
    #         recs = model.search([('module', '=', xrefs[0]),
    #                              ('name', '=', xrefs[1])])
    #         if recs:
    #             if retxref_id:
    #                 return recs[0].id
    #             return recs[0].res_id
    #     return False
    #
    # @api.model
    # def add_xref(self, xref, model, res_id):
    #     xrefs = xref.split('.')
    #     if len(xrefs) != 2:
    #         raise UserError(
    #             'Invalid xref %s' % xref)
    #     vals = {
    #         'module': xrefs[0],
    #         'name': xrefs[1],
    #         'model': model,
    #         'res_id': res_id
    #     }
    #     model_model = self.pool['ir.model.data']
    #     id = self.env_ref(xref, retxref_id=True)
    #     if not id:
    #         self.ctr_rec_new += 1
    #         return model_model.create(vals)
    #     model_model.browse(id).model_model.write(vals)
    #     self.ctr_rec_upd += 1
    #     return id
    #
    # def get_module_list(self):
    #     module_list = []
    #     for item in MODULES_NEEDED.keys():
    #         if not item or getattr(self, item):
    #             if isinstance(MODULES_NEEDED[item], (list, tuple)):
    #                 module_list += MODULES_NEEDED[item]
    #             elif isinstance(MODULES_NEEDED[item], dict):
    #                 module_list += MODULES_NEEDED[item].get(getattr(self, item))
    #     if not any([x for x in module_list if x in COA_MODULES]):
    #         module_list.append('l10n_it_fiscal')
    #     return module_list
    #
    # @api.model
    # def install_modules(self, modules_to_install):
    #     modules_to_install = list(set(modules_to_install))
    #     modules_model = self.pool['ir.module.module']
    #     to_install_modules = modules_model
    #     for module in modules_to_install:
    #         module_ids = modules_model.search([('name', '=', module)])
    #         if module_ids and module_ids[0].state == 'uninstalled':
    #             if len(modules_to_install) != 1 and module in COA_MODULES:
    #                 # CoA modules must be installed before others
    #                 self.install_modules([module])
    #                 continue
    #             to_install_modules += module_ids[0]
    #             self.status_mesg += 'Module %s installed\n' % module
    #     max_time_to_wait = 5
    #     if to_install_modules:
    #         to_install_modules.button_immediate_install()
    #         max_time_to_wait = 4 * len(to_install_modules) + 5
    #     while max_time_to_wait > 0:
    #         time.sleep(1)
    #         max_time_to_wait -= 1
    #         found_uninstalled = False
    #         for module in modules_to_install:
    #             module_ids = modules_model.search([('name', '=', module)])
    #             if not module_ids or module_ids[0].state != 'installed':
    #                 found_uninstalled = module
    #                 break
    #     if found_uninstalled:
    #         raise UserError(
    #             'Module %s not installed!' % found_uninstalled)
    #     return
    #
    # @api.model
    # def get_tnldict(self):
    #     if not hasattr(self, 'tnldict'):
    #         self.tnldict = {}
    #         transodoo.read_stored_dict(self.tnldict)
    #     return self.tnldict
    #
    # @api.model
    # def setup_model_structure(self, model):
    #     """Store model structure into memory"""
    #     if not model:
    #         return
    #     if model in self.STRUCT:
    #         return
    #     self.STRUCT[model] = self.pool[model].fields_get()
    #     # self.STRUCT[model] = self.STRUCT.get(model, {})
    #     # for field in self.pool['ir.model.fields'].search(
    #     #         [('model', '=', model)]):
    #     #     attrs = {}
    #     #     for attr in ('required', 'readonly'):
    #     #         attrs[attr] = field[attr]
    #     #     if attrs['required']:
    #     #         attrs['readonly'] = False
    #     #     if (field.ttype in ('binary', 'reference') or
    #     #             (hasattr(field, 'related') and field.related and
    #     #              not field.required)):
    #     #         attrs['readonly'] = True
    #     #     attrs['ttype'] = field.ttype
    #     #     attrs['relation'] = field.relation
    #     #     self.STRUCT[model][field.name] = attrs
    #
    # @api.model
    # def get_domain_field(self, model, vals, company_id,
    #                      field=None, parent_id=None, parent_name=None):
    #     for nm in ('code', 'acc_number', 'login', 'description', 'origin',
    #                'sequence', 'name'):
    #         if nm == 'code' and model == 'product.product':
    #             continue
    #         if nm in vals and nm in self.STRUCT[model]:
    #             break
    #     domain = [(nm, '=', vals[field or nm])]
    #     if 'company_id' in self.STRUCT[model]:
    #         domain.append(('company_id', '=', company_id))
    #     if parent_id and parent_name in self.STRUCT[model]:
    #         domain.append((parent_name, '=', parent_id))
    #     recs = self.pool[model].search(domain, context={'lang': 'en_US'})
    #     if len(recs) == 1:
    #         return recs[0].id
    #     return False
    #
    # @api.model
    # def bind_fields(self, model, vals, company_id,
    #                 parent_id=None, parent_model=None):
    #     self.setup_model_structure(model)
    #     model_model = self.pool[model]
    #     parent_name = ''
    #     for field in vals.copy():
    #         attrs = self.STRUCT[model].get(field, {})
    #         if not attrs:
    #             if (model == 'account.payment.term.line' and
    #                     field == 'months' and
    #                     vals[field]):
    #                 vals['days'] = (eval(vals[field]) * 30) - 2
    #             del vals[field]
    #             continue
    #         if (model == 'account.account' and
    #                 field == 'id' and
    #                 vals[field].startswith('z0bug.')):
    #             xrefs = vals[field].split('.')
    #             vals[field] = self.env_ref(vals[field])
    #             if not vals[field]:
    #                 tok = '_%s' % xrefs[1]
    #                 recs = self.pool['ir.model.data'].search(
    #                     [('module', '=', 'l10n_it_fiscal'),
    #                      ('name', 'like', r'_\%s' % tok),
    #                      ('model', '=', 'account.account')])
    #                 for xref in recs:
    #                     if xref.name.endswith(tok):
    #                         acc = model_model.browse(xref.res_id)
    #                         if acc.company_id.id == company_id:
    #                             vals[field] = acc.id
    #                             break
    #             if 'user_type_id' in vals:
    #                 if self.STRUCT[model].get('nature', {}):
    #                     if isinstance(vals['user_type_id'], int):
    #                         acc = self.pool['account.account.type'].browse(
    #                             vals['user_type_id'])
    #                     else:
    #                         acc = self.pool['account.account.type'].browse(
    #                             self.env_ref(vals['user_type_id']))
    #                     if acc.nature:
    #                         vals['nature'] = acc.nature
    #             continue
    #         elif model == 'account.payment.term.line' and field == 'option':
    #             if (vals[field] == 'fix_day_following_month' and
    #                     eval(release.major_version.split('.')[0]) >= 12):
    #                 vals[field] = 'day_following_month'
    #         elif field == 'id':
    #             continue
    #         elif parent_id and (
    #                 (parent_model and
    #                  attrs.get('relation', '/') == parent_model) or
    #                 (not parent_model and
    #                  attrs.get('relation', '/') == model)):
    #             vals[field] = parent_id
    #             parent_name = field
    #         elif field == 'company_id':
    #             vals[field] = company_id
    #             continue
    #         elif attrs['type'] in ('many2one', 'one2many', 'many2many'):
    #             if len(vals[field].split('.')) == 2:
    #                 if attrs['type'] == 'many2one':
    #                     vals[field] = self.env_ref(vals[field])
    #                 else:
    #                     vals[field] = [(6, 0, [self.env_ref(vals[field])])]
    #             continue
    #         elif attrs['type'] == 'boolean':
    #             vals[field] = os0.str2bool(vals[field], False)
    #         elif attrs['type'] == 'date':
    #             if vals[field].startswith('+'):
    #                 vals[field] = str(
    #                     date.today() + timedelta(int(vals[field][1:])))
    #             elif vals[field].startswith('-'):
    #                 vals[field] = str(
    #                     date.today() - timedelta(int(vals[field][1:])))
    #             elif vals[field].find('<#') >= 0:
    #                 items = vals[field].split('-')
    #                 for i, item in enumerate(items):
    #                     if item == '<#':
    #                         if i == 0:
    #                             items[i] = date.today().year - 1
    #                         elif i == 1:
    #                             items[i] = date.today().month - 1
    #                         elif i == 2:
    #                             items[i] = date.today().day - 1
    #                     else:
    #                         items[i] = int(items[i])
    #                 if len(items) > 1:
    #                     if items[2] < 1:
    #                         items[1] -= 1
    #                     if items[1] < 1:
    #                         items[1] = 12
    #                         items[0] -= 1
    #                     if items[2] < 1:
    #                         items[2] = calendar.monthrange(items[0],
    #                                                        items[1])[1]
    #                 vals[field] = '%04d-%02d-%02d' % (
    #                     items[0], items[1], items[2])
    #             elif vals[field].find('#>') >= 0:
    #                 items = vals[field].split('-')
    #                 for i, item in enumerate(items):
    #                     if item == '#>':
    #                         if i == 0:
    #                             items[i] = date.today().year + 1
    #                         elif i == 1:
    #                             items[i] = date.today().month + 1
    #                         elif i == 2:
    #                             items[i] = date.today().day + 1
    #                     else:
    #                         items[i] = int(items[i])
    #                 if len(items) > 1:
    #                     if items[1] > 12:
    #                         items[1] = 1
    #                         items[0] += 1
    #                     if items[2] > calendar.monthrange(items[0],
    #                                                       items[1])[1]:
    #                         items[2] = 1
    #                         items[1] += 1
    #                         if items[1] > 12:
    #                             items[1] = 1
    #                             items[0] += 1
    #                 vals[field] = '%04d-%02d-%02d' % (
    #                     items[0], items[1], items[2])
    #             elif vals[field].find('#') >= 0:
    #                 items = vals[field].split('-')
    #                 for i, item in enumerate(items):
    #                     if item == '#':
    #                         if i == 0:
    #                             items[i] = date.today().year
    #                         elif i == 1:
    #                             items[i] = date.today().month
    #                         elif i == 2:
    #                             items[i] = date.today().day
    #                     else:
    #                         items[i] = int(items[i])
    #                 vals[field] = '%04d-%02d-%02d' % (
    #                     items[0], items[1], items[2])
    #         elif attrs['type'] == 'datetime':
    #             if vals[field].startswith('+'):
    #                 vals[field] = str(
    #                     datetime.today() + timedelta(int(vals[field][1:])))
    #             elif vals[field].startswith('-'):
    #                 vals[field] = str(
    #                     datetime.today() - timedelta(int(vals[field][1:])))
    #         elif attrs.get('relation'):
    #             self.setup_model_structure(attrs['relation'])
    #             value = self.get_domain_field(model, vals, company_id,
    #                                           field=field)
    #             if value:
    #                 vals[field] = value
    #             else:
    #                 del vals[field]
    #     if parent_id and parent_model:
    #         vals['id'] = self.get_domain_field(
    #             model, vals, company_id,
    #             parent_id=parent_id, parent_name=parent_name)
    #         if not vals['id']:
    #             del vals['id']
    #     if (vals.get('id') and self.load_image and
    #             'image' in self.STRUCT[model]):
    #         filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(
    #             vals['id'])
    #         if filename:
    #             vals['image'] = z0bug_odoo_lib.Z0bugOdoo().get_image(
    #                 vals['id'])
    #     return vals, parent_name
    #
    # @api.model
    # def drop_unchanged_fields(self, vals, model, xid):
    #     rec = None
    #     if model and xid:
    #         rec = self.pool[model].browse(xid)
    #     for field in vals.copy():
    #         attrs = self.STRUCT[model].get(field, {})
    #         if not attrs:
    #             del vals[field]
    #         if rec:
    #             if attrs['type'] == 'many2one':
    #                 if ((rec[field] and vals[field] == rec[field].id) or
    #                         (not rec[field] and not vals[field])):
    #                     del vals[field]
    #             elif attrs['type'] == 'boolean':
    #                 if isinstance(
    #                         vals[field], bool) and vals[field] == rec[field]:
    #                     del vals[field]
    #                 elif os0.str2bool(vals[field], False) == rec[field]:
    #                     del vals[field]
    #             elif (isinstance(vals[field], (basestring, int)) and
    #                   vals[field] == rec[field]):
    #                 del vals[field]
    #     return vals
    #
    # @api.model
    # def write_diff(self, model, xid, vals):
    #     vals = self.drop_unchanged_fields(vals, model, xid)
    #     if vals:
    #         if 'id' in vals:
    #             del vals['id']
    #         self.pool[model].browse(xid).write(vals)
    #         self.ctr_rec_upd += 1
    #
    # @api.model
    # def store_xref(self, xref, model, company_id,
    #                parent_id=None, parent_model=None, seq=None):
    #     if parent_id and parent_model:
    #         xid = False
    #     else:
    #         xid = self.env_ref(xref)
    #     if not xid or self.force_test_values:
    #         vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
    #         # TODO > Hotfix
    #         if model == 'account.payment.term.line':
    #             if (vals['option'] == 'fix_day_following_month' and
    #                     eval(release.major_version.split('.')[0]) >= 12):
    #                 vals['option'] = 'after_invoice_month'
    #         if seq:
    #             vals['sequence'] = seq
    #         vals, parent_name = self.bind_fields(
    #             model, vals, company_id,
    #             parent_id=parent_id, parent_model=parent_model)
    #         if xid:
    #             self.write_diff(model, xid, vals)
    #         else:
    #             if vals.get('id') and isinstance(vals['id'], int):
    #                 xid = vals['id']
    #             else:
    #                 xid = self.get_domain_field(model, vals, company_id,
    #                                             parent_id=parent_id,
    #                                             parent_name=parent_name)
    #             if xid:
    #                 self.write_diff(model, xid, vals)
    #             else:
    #                 if 'id' in vals:
    #                     del vals['id']
    #                 try:
    #                     xid = self.pool[model].create(vals).id
    #                     self.ctr_rec_new += 1
    #                 except BaseException as e:
    #                     self._cr.rollback()  # pylint: disable=invalid-commit
    #                     self.status_mesg += ('Error %s\n' % e)
    #                     xid = False
    #                     raise UserError(self.status_mesg)
    #             if xid and (not parent_id or not parent_model):
    #                 self.add_xref(xref, model, xid)
    #     return xid
    #
    # @api.model
    # def make_model(self, company_id, model, mode=None, model2=None):
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     for xref in sorted(xrefs):
    #         self.store_xref(xref, model, company_id)
    #     self._cr.commit()                      # pylint: disable=invalid-commit
    #
    # @api.model
    # def mk_account_account(self, company_id):
    #     model = 'account.account'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     for xref in sorted(xrefs):
    #         # Prima i mastri
    #         if len(xref) == 12:
    #             self.store_xref(xref, model, company_id)
    #     for xref in xrefs:
    #         # poi i capoconti
    #         if len(xref) == 13:
    #             self.store_xref(xref, model, company_id)
    #     for xref in xrefs:
    #         # infine i sottoconti
    #         if len(xref) > 13:
    #             self.store_xref(xref, model, company_id)
    #
    # @api.model
    # def mk_account_tax(self, company_id):
    #     self.make_model(company_id, 'account.tax')
    #
    # @api.model
    # def mk_fiscal_position(self, company_id):
    #     self.make_model(company_id, 'account.fiscal.position')
    #
    # @api.model
    # def mk_journal(self, company_id):
    #     self.make_model(company_id, 'account.journal')
    #
    # @api.model
    # def mk_date_range(self, company_id):
    #     self.make_model(company_id, 'date.range.type')
    #     self.make_model(company_id, 'date.range')
    #
    # @api.model
    # def mk_payment(self, company_id):
    #     model = 'account.payment.term'
    #     model2 = 'account.payment.term.line'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
    #     parent_id = False
    #     for xref in sorted(xrefs):
    #         if len(xref) == 15:
    #             parent_id = self.store_xref(xref, model, company_id)
    #             seq = 10
    #             model_model = self.pool['account.payment.term.line']
    #             for payment_line in model_model.search(
    #                     [('payment_id', '=', parent_id)],
    #                     order='sequence,id'):
    #                 payment_line.write({'sequence': seq})
    #                 seq += 10
    #         else:
    #             self.store_xref(xref, model2, company_id,
    #                             parent_id=parent_id, parent_model=model)
    #
    # @api.model
    # def mk_partner(self, company_id):
    #     model = 'res.partner'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     parent_id = False
    #     for xref in sorted(xrefs):
    #         if len(xref) <= 20 or xref == 'z0bug.partner_mycompany':
    #             parent_id = self.store_xref(xref, model, company_id)
    #         else:
    #             parent_id = self.env_ref(xref[:-2])
    #             self.store_xref(xref, model, company_id, parent_id=parent_id)
    #     self._cr.commit()  # pylint: disable=invalid-commit
    #
    # @api.model
    # def mk_partner_bank(self, company_id):
    #     self.make_model(company_id, 'res.partner.bank')
    #
    # @api.model
    # def mk_product(self, company_id):
    #     model = 'product.template'
    #     model2 = 'product.product'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     for xref in sorted(xrefs):
    #         self.store_xref(xref, model, company_id)
    #         xref2 = xref.replace('z0bug.product_template',
    #                              'z0bug.product_product')
    #         self.store_xref(xref2, model2, company_id)
    #
    # @api.model
    # def mk_account_invoice(self, company_id):
    #
    #     def compute_tax(inv_id):
    #         self.pool['account.invoice'].browse(inv_id).compute_taxes()
    #
    #     model = 'account.invoice'
    #     model2 = 'account.invoice.line'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
    #     parent_id = False
    #     for xref in sorted(xrefs):
    #         if len(xref) <= 19:
    #             if parent_id:
    #                 compute_tax(parent_id)
    #             parent_id = self.store_xref(xref, model, company_id)
    #         else:
    #             self.store_xref(xref, model2, company_id,
    #                             parent_id=parent_id, parent_model=model)
    #     if parent_id:
    #         compute_tax(parent_id)
    #
    # @api.model
    # def mk_sale_order(self, company_id):
    #
    #     def compute_tax(inv_id):
    #         return
    #
    #     model = 'sale.order'
    #     model2 = 'sale.order.line'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
    #     parent_id = False
    #     seq = 0
    #     for xref in sorted(xrefs):
    #         if len(xref) <= 22:
    #             if parent_id:
    #                 compute_tax(parent_id)
    #             seq = 0
    #             parent_id = self.store_xref(xref, model, company_id)
    #         else:
    #             if self.set_seq:
    #                 seq += 10
    #             else:
    #                 seq = 10
    #             self.store_xref(xref, model2, company_id,
    #                             parent_id=parent_id, parent_model=model,
    #                             seq=seq)
    #     if parent_id:
    #         compute_tax(parent_id)
    #
    # @api.model
    # def mk_purchase_order(self, company_id):
    #
    #     def compute_tax(inv_id):
    #         return
    #
    #     model = 'purchase.order'
    #     model2 = 'purchase.order.line'
    #     xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
    #     xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
    #     parent_id = False
    #     parent_id_len = 0
    #     for xref in sorted(xrefs):
    #         if (not parent_id_len or
    #                 len(xref) <= parent_id_len):
    #             if not parent_id_len:
    #                 parent_id_len = len(xref) + 1
    #             if parent_id:
    #                 compute_tax(parent_id)
    #             parent_id = self.store_xref(xref, model, company_id)
    #         else:
    #             self.store_xref(xref, model2, company_id,
    #                             parent_id=parent_id, parent_model=model)
    #     if parent_id:
    #         compute_tax(parent_id)
    #
    # @api.model
    # def create_company(self):
    #     vals = {
    #         'name': 'Test Company',
    #     }
    #     company = self.pool['res.company'].create(vals)
    #     self.ctr_rec_new += 1
    #     self.set_company_to_test(company)
    #
    # @api.model
    # def set_company_to_test(self, company):
    #     self.add_xref('z0bug.mycompany', 'res.company', company.id)
    #     self.add_xref(
    #         'z0bug.partner_mycompany', 'res.partner', company.partner_id.id)

    def make_test_environment(self, cr, uid, ids, context=None):
        # wiz_id = context.get('active_id', False)
        # wiz = self.browse(cr, uid, ids[0], context=context)
        # self._cr = cr
        # self._uid = uid
        # self.wiz.ctr_rec_new = 0
        # self.wiz.ctr_rec_upd = 0
        # self.wiz.ctr_rec_del = 0
        # self.wiz.status_mesg = ''
        # modules_to_install = self.get_module_list()
        # self.install_modules(modules_to_install)
        # if self.wiz.new_company:
        #     self.create_company()
        # elif not self.wiz.test_company_id:
        #     self.set_company_to_test(self.wiz.company_id)
        # if self.wiz.load_coa and self.wiz.coa in ('test', 'powerp'):
        #     self.mk_account_account(self.wiz.company_id.id)
        #     self.mk_account_tax(self.wiz.company_id.id)
        # if self.wiz.load_coa == 'coa':
        #     self.mk_fiscal_position(self.wiz.company_id.id)
        #     self.mk_date_range(self.wiz.company_id.id)
        #     self.mk_payment(self.wiz.company_id.id)
        # if self.wiz.load_partner:
        #     self.mk_partner(self.wiz.company_id.id)
        #     self.mk_partner_bank(self.wiz.company_id.id)
        #     self.mk_journal(self.wiz.company_id.id)
        # if self.wiz.load_product:
        #     self.mk_product(self.wiz.company_id.id)
        # if self.wiz.load_sale_order:
        #     self.mk_sale_order(self.wiz.company_id.id)
        # if self.wiz.load_purchase_order:
        #     self.mk_purchase_order(self.wiz.company_id.id)
        # if self.wiz.load_invoice:
        #     self.mk_account_invoice(self.wiz.company_id.id)
        # self.wiz.status_mesg += 'Data (re)loaded'
        return {
            'name': "Data created",
            'type': 'ir.actions.act_window',
            'res_model': 'self.wizard.make.test.environment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': ids[0],
            'target': 'new',
            'context': {'active_id': ids[0]},
            'view_id': self.pool.get('ir.model.data').get_object_reference(
                cr, uid, 'mk_test_env', 'result_mk_test_env_view')[1],
            'domain': [('id', '=', ids[0])],
        }

    @api.model
    def close_window(self):
        return
