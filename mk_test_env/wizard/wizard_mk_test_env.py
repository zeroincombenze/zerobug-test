# -*- coding: utf-8 -*-
#
# Copyright 2019-21 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from past.builtins import basestring
from builtins import int
# import os
from datetime import date, datetime, timedelta
import time
import calendar
import re

from odoo import api, fields, models
from odoo.exceptions import UserError

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
    'load_sp': ['l10n_it_split_payment'],
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
COMMIT_FCT = {
    'account.invoice': {
        'cancel': ['action_invoice_draft'],
        'draft': ['compute_taxes', 'action_invoice_open'],
    },
    'sale.order': {
        'cancel': ['action_invoice_draft'],
        'draft': ['action_confirm'],
    }
}
DRAFT_FCT = {
    'account.invoice': {
        'paid': ['action_invoice_re_open'],
        'open': ['action_invoice_cancel'],
        'cancel': ['action_invoice_draft'],
    },
    'sale.order': {
        'sale': ['action_cancel'],
        'cancel': ['action__draft'],
    }
}

class WizardMakeTestEnvironment(models.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"

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
    load_sp = fields.Boolean('Activate Split Payment')
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
    status_mesg = fields.Text('Installation status',
                              readonly=True)

    @api.model
    def env_ref(self, xref, retxref_id=None, company_id=None, model=None):
        # We do not use standard self.env.ref() because we need False value
        # if xref does not exits instead of exception
        # and we need to get id or record by parameter
        # if (xref == 'product.product_uom_unit' and
        #         eval(release.major_version.split('.')[0]) >= 12):
        #     xref = 'uom.product_uom_unit'
        xrefs = self.translate('', xref, ttype='xref').split('.')
        if len(xrefs) == 2 and ' ' not in xref:
            ir_model = self.env['ir.model.data']
            recs = ir_model.search([('module', '=', xrefs[0]),
                                    ('name', '=', xrefs[1])])
            if recs:
                if retxref_id:
                    return recs[0].id
                return recs[0].res_id
            elif model:
                if (model == 'account.account' and
                        xref.startswith('z0bug.coa_')):
                    tok = '_%s' % xrefs[1].split('_')[1]
                    recs = ir_model.search(
                        [('module', '=', 'l10n_it_fiscal'),
                         ('name', 'like', r'_\%s' % tok),
                         ('model', '=', 'account.account')])
                    for xid in recs:
                        if xid.name.endswith(tok):
                            rec = self.env[model].browse(xid.res_id)
                            if rec.company_id.id == company_id:
                                if retxref_id:
                                    return xid.id
                                return xid.res_id
                elif (model == 'account.tax' and
                        xref.startswith('z0bug.tax_')):
                    tok = '_%s' % xrefs[1].split('_')[1]
                    recs = ir_model.search(
                        [('module', '=', 'l10n_it_fiscal'),
                         ('name', 'like', r'_\%s' % tok),
                         ('model', '=', 'account.tax')])
                    for xid in recs:
                        if xid.name.endswith(tok):
                            rec = self.env[model].browse(xid.res_id)
                            if rec.company_id.id == company_id:
                                if retxref_id:
                                    return xid.id
                                return xid.res_id
        return False

    @api.model
    def add_xref(self, xref, model, res_id):
        xrefs = xref.split('.')
        if len(xrefs) != 2 or ' ' in xref:
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
        model_model.browse(id).write(vals)
        self.ctr_rec_upd += 1
        return id

    def get_module_list(self):
        module_list = []
        for item in MODULES_NEEDED.keys():
            if not item or getattr(self, item):
                if isinstance(MODULES_NEEDED[item], (list, tuple)):
                    module_list += MODULES_NEEDED[item]
                elif isinstance(MODULES_NEEDED[item], dict):
                    module_list += MODULES_NEEDED[item].get(getattr(self, item))
        if not any([x for x in module_list if x in COA_MODULES]):
            module_list.append('l10n_it_fiscal')
        module_list = [self.translate('', module, ttype='module')
                       for module in module_list]
        return module_list

    @api.model
    def install_modules(self, modules_to_install):
        modules_to_install = list(set(modules_to_install))
        modules_model = self.env['ir.module.module']
        to_install_modules = modules_model
        for module in modules_model.search(
                [('name', 'in', modules_to_install)]):
            if module and module.state == 'uninstalled':
                if len(modules_to_install) != 1 and module in COA_MODULES:
                    # CoA modules must be installed before others
                    self.install_modules([module])
                    continue
                to_install_modules += module
                self.status_mesg += 'Module %s installed\n' % module.name
        max_time_to_wait = 5
        if to_install_modules:
            to_install_modules.button_immediate_install()
            max_time_to_wait = 4 * len(to_install_modules) + 5
        found_uninstalled = True
        while max_time_to_wait > 0 and found_uninstalled:
            time.sleep(1)
            max_time_to_wait -= 1
            found_uninstalled = False
            for module in modules_model.search(
                    [('name', 'in', modules_to_install)]):
                if not module or module.state == 'uninstalled':
                    found_uninstalled = module
                    break
        if found_uninstalled:
            raise UserError(
                'Module %s not installed!' % found_uninstalled.name)
        return

    def get_tnldict(self):
        if not hasattr(self, 'tnldict'):
            self.tnldict = {}
            transodoo.read_stored_dict(self.tnldict)
        return self.tnldict

    def translate(self, model, src, ttype=False, fld_name=False):
        if release.major_version == '10.0':
            if ttype == 'valuetnl':
                return ''
            return src
        return transodoo.translate_from_to(
            self.get_tnldict(),
            model, src, '10.0', release.major_version,
            ttype=ttype, fld_name=fld_name)

    def setup_model_structure(self, model):
        """Store model structure into memory"""
        if not model:
            return
        if model in self.STRUCT:
            return
        self.STRUCT[model] = self.env[model].fields_get()
        # self.STRUCT[model] = self.STRUCT.get(model, {})
        # for field in self.env['ir.model.fields'].search(
        #         [('model', '=', model)]):
        #     attrs = {}
        #     for attr in ('required', 'readonly'):
        #         attrs[attr] = field[attr]
        #     if attrs['required']:
        #         attrs['readonly'] = False
        #     if (field.ttype in ('binary', 'reference') or
        #             (hasattr(field, 'related') and field.related and
        #              not field.required)):
        #         attrs['readonly'] = True
        #     attrs['ttype'] = field.ttype
        #     attrs['relation'] = field.relation
        #     self.STRUCT[model][field.name] = attrs

    def bind_record(self, model, vals, company_id,
                    field=None, parent_id=None, parent_name=None):
        domain = []
        for nm in ('code', 'acc_number', 'login', 'description', 'name',
                   'number', 'sequence'):
            if nm == 'code' and model == 'product.product':
                continue
            elif nm == 'description' and model == 'account.tax':
                continue
            elif nm == 'sequence' and not parent_id and not parent_name:
                continue
            if nm in vals and nm in self.STRUCT[model]:
                domain.append((nm, '=', vals[field or nm]))
                if not parent_id or parent_name not in self.STRUCT[model]:
                    break
        if domain:
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
        if (self.load_image and vals.get('id') and
                'image' in self.STRUCT[model]):
            filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(
                vals['id'])
            if filename:
                vals['image'] = z0bug_odoo_lib.Z0bugOdoo().get_image(
                    vals['id'])
        parent_name = ''
        for field in vals.copy().keys():
            if vals[field] == 'None':
                del vals[field]
                continue
            if self.translate(model, field, ttype='valuetnl', fld_name=field):
                vals[field] = self.translate(
                    model, vals[field], ttype='value', fld_name=field)
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                #     # Odoo without payment term extension
                #     if (model == 'account.payment.term.line' and
                #             field == 'months' and
                #             vals[field]):
                #         vals['days'] = (eval(vals[field]) * 30) - 2
                del vals[field]
                self.status_mesg += 'Model %s w/o field %s\n' % (model, field)
                continue
            if field == 'id':
                if parent_id and parent_model:
                    del vals[field]
                elif isinstance(vals[field], basestring):
                    if vals[field].isdigit():
                        vals[field] = eval(vals[field])
                    else:
                        vals[field] = self.env_ref(vals[field],
                                       company_id=company_id,
                                       model=model)
                    if not vals[field]:
                        del vals[field]
            elif parent_id and (
                    (parent_model and
                     attrs.get('relation', '/') == parent_model) or
                    (not parent_model and
                     attrs.get('relation', '/') == model)):
                vals[field] = parent_id
                parent_name = field
            elif field == 'company_id':
                vals[field] = company_id
                continue
            elif attrs['type'] in ('many2one', 'one2many', 'many2many'):
                if len(vals[field].split('.')) == 2 and ' ' not in vals[field]:
                    xid = self.env_ref(vals[field],
                                       company_id=company_id,
                                       model=attrs['relation'])
                    if attrs['type'] == 'many2one':
                        vals[field] = xid
                    elif xid:
                        vals[field] = [(6, 0, [xid])]
                continue
            elif attrs['type'] == 'boolean':
                vals[field] = os0.str2bool(vals[field], False)
            elif attrs['type'] == 'date':
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
                        else:
                            items[i] = int(items[i])
                    if len(items) > 1:
                        if items[2] < 1:
                            items[1] -= 1
                        if items[1] < 1:
                            items[1] = 12
                            items[0] -= 1
                        if items[2] < 1:
                            items[2] = calendar.monthrange(items[0],
                                                           items[1])[1]
                    vals[field] = '%04d-%02d-%02d' % (
                        items[0], items[1], items[2])
                elif vals[field].find('#>') >= 0:
                    items = vals[field].split('-')
                    for i, item in enumerate(items):
                        if item == '#>':
                            if i == 0:
                                items[i] = date.today().year + 1
                            elif i == 1:
                                items[i] = date.today().month + 1
                            elif i == 2:
                                items[i] = date.today().day + 1
                        else:
                            items[i] = int(items[i])
                    if len(items) > 1:
                        if items[1] > 12:
                            items[1] = 1
                            items[0] += 1
                        if items[2] > calendar.monthrange(items[0],
                                                          items[1])[1]:
                            items[2] = 1
                            items[1] += 1
                            if items[1] > 12:
                                items[1] = 1
                                items[0] += 1
                    vals[field] = '%04d-%02d-%02d' % (
                        items[0], items[1], items[2])
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
                        else:
                            items[i] = int(items[i])
                    vals[field] = '%04d-%02d-%02d' % (
                        items[0], items[1], items[2])
            elif attrs['type'] == 'datetime':
                if vals[field].startswith('+'):
                    vals[field] = str(
                        datetime.today() + timedelta(int(vals[field][1:])))
                elif vals[field].startswith('-'):
                    vals[field] = str(
                        datetime.today() - timedelta(int(vals[field][1:])))
            elif attrs.get('relation'):
                self.setup_model_structure(attrs['relation'])
                value = self.bind_record(model, vals, company_id,
                                         field=field)
                if value:
                    vals[field] = value
                else:
                    del vals[field]
        if model == 'account.account':
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
        if parent_id and parent_model:
            vals['id'] = self.bind_record(
                model, vals, company_id,
                parent_id=parent_id, parent_name=parent_name)
            if not vals['id']:
                del vals['id']
        return vals, parent_name

    def drop_unchanged_fields(self, vals, model, xid):
        rec = None
        if model and xid:
            rec = self.env[model].browse(xid)
        for field in vals.copy():
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                del vals[field]
            if isinstance(vals[field], basestring) and vals[field]:
                if attrs['type'] in ('float', 'integer'):
                    vals[field] = eval(vals[field])
            if rec:
                if attrs['type'] == 'many2one':
                    if ((rec[field] and vals[field] == rec[field].id) or
                            (not rec[field] and not vals[field])):
                        del vals[field]
                elif attrs['type'] == 'boolean':
                    if isinstance(
                            vals[field], bool) and vals[field] == rec[field]:
                        del vals[field]
                    elif os0.str2bool(vals[field], False) == rec[field]:
                        del vals[field]
                elif (isinstance(vals[field],
                                 (basestring, int, float, date, datetime)) and
                      (vals[field] == rec[field]) or
                      (not rec[field] and not vals[field])):
                    del vals[field]
        return vals

    @api.model
    def write_diff(self, model, xid, vals, parent_id=None, parent_model=None):
        vals = self.drop_unchanged_fields(vals, model, xid)
        if 'id' in vals:
            del vals['id']
        if vals:
            if parent_model and parent_id:
                self.do_draft(parent_model, parent_id)
            else:
                self.do_draft(model, xid)
            self.env[model].browse(xid).write(vals)
            self.ctr_rec_upd += 1

    @api.model
    def store_xref(self, xref, model, company_id,
                   parent_id=None, parent_model=None, seq=None):
        if parent_id and parent_model:
            xid = False
        else:
            xid = self.env_ref(xref, company_id=company_id, model=model)
        if not xid or self.force_test_values:
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
            if 'sequence' in self.STRUCT[model] and seq:
                vals['sequence'] = seq
            vals, parent_name = self.bind_fields(
                model, vals, company_id,
                parent_id=parent_id, parent_model=parent_model)
            if xid:
                self.write_diff(model, xid, vals,
                                parent_id=parent_id, parent_model=parent_model)
            else:
                if vals.get('id') and isinstance(vals['id'], int):
                    xid = vals['id']
                else:
                    xid = self.bind_record(model, vals, company_id,
                                           parent_id=parent_id,
                                           parent_name=parent_name)
                if xid:
                    self.write_diff(model, xid, vals,
                                    parent_id=parent_id, parent_model=parent_model)
                else:
                    if 'id' in vals:
                        del vals['id']
                    try:
                        xid = self.env[model].create(vals).id
                        self.ctr_rec_new += 1
                    except BaseException as e:
                        self._cr.rollback()  # pylint: disable=invalid-commit
                        self.status_mesg += ('Error %s\n' % e)
                        xid = False
                        raise UserError(self.status_mesg)
                if xid and (not parent_id or not parent_model):
                    self.add_xref(xref, model, xid)
        return xid

    @api.model
    def do_workflow(self, model, rec_id, FCT):
        if model in FCT:
            rec = self.env[model].browse(rec_id)
            while rec.state in FCT[model]:
                old_state = rec.state
                for action in FCT[model][old_state]:
                    if hasattr(self.env[model], action):
                        getattr(rec, action)()
                        if not action.startswith('action'):
                            rec.write({})
                # We need to invalidate cache due burst state read
                # self.env.invalidate_all()
                rec = self.env[model].browse(rec_id)
            return

    @api.model
    def do_draft(self, model, rec_id):
        self.do_workflow(model, rec_id, DRAFT_FCT)

    @api.model
    def do_commit(self, model, rec_id):
        self.do_workflow(model, rec_id, COMMIT_FCT)

    @api.model
    def make_model(self, company_id, model, mode=None, model2=None):
        self.setup_model_structure(model)
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        if model2:
            self.setup_model_structure(model2)
            xrefs = xrefs + z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model2)
        # z0bug xref has format "MODULE.LABEL_N" where N is a number 1..999
        # When xref is child of a parent table,
        # xref has format "MODULE.LABEL_N_M" where M ia a number 1..999
        seq = 0
        parent_id = False
        for xref in sorted(xrefs):
            if re.match('.*_[0-9]+_[0-9]+$', xref):
                # Found child xref, evaluate parent xref
                parent_id = self.env_ref('_'.join(xref.split('_')[0:-1]))
                if self.set_seq:
                    seq += 10
                else:
                    seq = 10
                self.store_xref(xref, model2 or model, company_id,
                                parent_id=parent_id, parent_model=model,
                                seq=seq)
            else:
                if seq:
                    # Previous write was a detail record
                    self.do_commit(model, parent_id)
                parent_id = self.store_xref(xref, model, company_id)
                if model == 'account.payment.term':
                    seq = 10
                    model2_model = self.env[model2]
                    for rec_line in model2_model.search(
                            [('payment_id', '=', parent_id)],
                            order='sequence,id'):
                        rec_line.write({'sequence': seq})
                        seq += 10
                seq = 0
        if seq:
            self.do_commit(model, parent_id)
        self._cr.commit()                      # pylint: disable=invalid-commit

    @api.model
    def mk_account_account(self, company_id):
        model = 'account.account'
        self.setup_model_structure(model)
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

    @api.model
    def enable_cancel_journal(self):
        journal_model = self.env['account.journal']
        for rec in journal_model.search([('update_posted', '=', False)]):
            rec.write({'update_posted': True})

    def make_test_environment(self):
        self.ctr_rec_new = 0
        self.ctr_rec_upd = 0
        self.ctr_rec_del = 0
        self.status_mesg = ''
        modules_to_install = self.get_module_list()
        self.install_modules(modules_to_install)
        if self.new_company:
            self.create_company()
        elif not self.test_company_id:
            self.set_company_to_test(self.company_id)
        if self.load_coa and self.coa in ('test', 'powerp'):
            self.mk_account_account(self.company_id.id)
            self.make_model(self.company_id.id, 'account.tax')
        if self.load_coa == 'coa':
            self.make_model(self.company_id.id, 'decimal.precision')
            self.make_model(self.company_id.id, 'account.fiscal.position')
            self.make_model(self.company_id.id, 'date.range.type')
            self.make_model(self.company_id.id, 'date.range')
            self.make_model(self.company_id.id, 'account.payment.term',
                            model2='account.payment.term.line')
            self.make_model(self.company_id.id, 'account.journal')
            self.enable_cancel_journal()
            self.make_model(self.company_id.id, 'withholding.tax',
                            model2='withholding.tax.rate')
        if self.load_partner:
            self.make_model(self.company_id.id, 'res.partner')
            self.make_model(self.company_id.id, 'res.partner.bank')
        if self.load_product:
            self.make_model(self.company_id.id, 'product.template')
            self.make_model(self.company_id.id, 'product.product')
        if self.load_sale_order:
            self.make_model(self.company_id.id, 'sale.order',
                            model2='sale.order.line')
        if self.load_purchase_order:
            self.make_model(self.company_id.id, 'purchase.order',
                            model2='purchase.order.line')
        if self.load_invoice:
            self.make_model(self.company_id.id, 'account.invoice',
                            model2='account.invoice.line')
        self.status_mesg += 'Data (re)loaded\n'
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
