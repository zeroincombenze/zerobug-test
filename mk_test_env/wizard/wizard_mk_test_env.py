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
import os
from datetime import date, datetime, timedelta
import time
import calendar
import re

import pytz

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
    '*': ['calendar', 'mail', 'product', 'stock',
          'profile_common'],
    'coa': {
        'l10n_it': ['l10n_it'],
        'zero': ['l10n_it_fiscal'],
        'powerp': ['l10n_it_coa_base']
    },
    'distro': {
        'powerp': ['l10n_eu_account', 'assigned_bank', 'account_duedates',
                   'assets_management_plus', 'l10n_it_balance',
                   'l10n_it_efattura_sdi_2c', 'l10n_it_mastrini']
    },
    'load_sp': ['l10n_it_split_payment'],
    'load_rc': ['l10n_it_reverse_charge'],
    'load_li': ['l10n_it_lettera_intento'],
    'load_wh': ['l10n_it_withholding_tax'],
    'load_conai': ['l10n_it_conai'],
    'load_sct': ['account_banking_sepa_credit_transfer'],
    'load_sdd': ['account_banking_sepa_direct_debit'],
    'load_riba': ['l10n_it_ricevute_bancarie'],
    'load_vat': ['account_vat_period_end_statement',
                 'l10n_it_vat_registries',
                 'l10n_it_vat_communication',
                 'l10n_it_vat_statement_communication'],
    'load_fiscal': ['l10n_it_central_journal',
                    'l10n_it_intrastat',
                    'l10n_it_invoices_data_communication',
                    'l10n_it_invoices_data_communication_fatturapa'],
    'load_coa': {
        '*': ['account',
              'date_range',
              'account_payment_term_extension',
              'l10n_it_fiscalcode',
              'account_move_template'],
    },
    'load_product': {
        '*': ['product', 'stock']
    },
    'load_partner': {
        '*': ['partner_bank'],
    },
    'load_sale_order': {
        '*': ['sale', 'l10n_it_ddt']
    },
    'load_purchase_order': {
        '*': ['purchase'],
    },
    'load_invoice': {
        '*': [
            'account_accountant', 'account_cancel',
            'payment', 'l10n_it_einvoice_in', 'l10n_it_einvoice_out'
        ],
    },
}
MODULES_BY_DISTRO = {
    'account_vat_period_end_statement': 'l10n_it_vat_statement',
    'l10n_it_einvoice_in': 'l10n_it_fatturapa_in_improved',
    'l10n_it_einvoice_ou': 'l10n_it_fatturapa_out_improved',
    # 'l10n_it_reverse_charge': 'l10n_it_reverse_charge_plus',
    # 'l10n_it_split_payment': 'l10n_it_vat_statement_split_payment_plus',
    # 'l10n_it_withholding_tax': '',
    # 'l10n_it_intrastat': 'l10n_it_intrastat_plus',
    # 'l10n_it_intrastat_statement': 'l10n_it_intrastat_statement_plus'
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
UNIQUE_REFS = ['z0bug.partner_mycompany']

@api.model
def _lang_get(self):
    return self.env['res.lang'].get_available()
# put POSIX 'Etc/*' entries at the end to avoid confusing users - see bug 1086728
def _tz_get(self):
    return [(tz, tz) for tz in sorted(
        pytz.all_timezones,
        key=lambda tz: tz if not tz.startswith('Etc/') else '_')]


class WizardMakeTestEnvironment(models.TransientModel):
    _name = "wizard.make.test.environment"
    _description = "Create Test Environment"

    STRUCT = {}

    def _test_company(self):
        recs = self.env['ir.model.data'].search(
            [('module', '=', 'z0bug'),
             ('name', '=', 'mycompany')])
        if recs:
            return recs[0].res_id
        return False

    def _new_company(self):
        flag = False
        if not bool(self._test_company()):
            flag = bool(self.env['res.partner'].search(
                ['|', ('customer', '!=', False), ('supplier', '!=', False)]
            ))
        return flag

    def _default_company(self):
        return self._test_company() or self.env.user.company_id.id

    def _set_flag(self, item):
        module_list, modules_to_remove = self.get_module_list(item)
        flag = False
        for module in self.env['ir.module.module'].search(
                [('name', 'in', module_list)]):
            if module and module.state == 'uninstalled':
                flag = True
                break
        return flag

    def _set_coa_2_use(self):
        module_list = []
        for item in MODULES_NEEDED['coa'].keys():
            module_list += MODULES_NEEDED['coa'][item]
        coa = 'zero'
        for module in self.env['ir.module.module'].search(
                [('name', 'in', module_list)]):
            if module and module.state == 'installed':
                for item in MODULES_NEEDED['coa'].keys():
                    if module.name in MODULES_NEEDED['coa'][item]:
                        coa = item
                        break
        return coa

    def _set_distro(self):
        if self.coa == 'l10n_it':
            distro = 'odoo_ce'
        elif self.coa in ('zero', 'powerp'):
            distro = 'powerp' if release.version_info[0] >= 12 else 'zero'
        else:
            distro = 'odoo_ce'
        return distro

    def _set_tz(self):
        tz = self._context.get('tz')
        if not tz:
            try:
                tz = os.path.join(
                    *os.readlink('/etc/localtime').split('/')[-2:])
            except:
                tz = 'Europe/Rome'
        return tz

    state = fields.Selection(
        [('', 'Load modules'),
         ('1', 'Load general data'),
         ('2', 'Load structured data'),
         ('9', 'Result')],
        readonly=True)
    test_company_id = fields.Many2one(
        'res.company',
        string='Test Company',
        # readonly=True,
        default=_test_company)
    new_company = fields.Boolean('Create new company',
                                 default=_new_company)
    company_id = fields.Many2one('res.company',
                                 string='Company',
                                 required=True,
                                 default=_default_company)
    lang = fields.Selection(
        _lang_get,
        string='Language',
        default=os.environ.get('LANG', 'en_US').split('.')[0])
    tz = fields.Selection(
        _tz_get,
        string='Timezone',
        default=lambda self: self._set_tz())
    coa = fields.Selection(
        [('l10n_it', 'Default Odoo CoA'),
         ('zero', 'Zeroincombenze CoA'),
         ('powerp', 'No chart of account')],
        'Chart of Account',
        help='Select Chart od Account to install\n'
             '"Default Odoo Chart Account" (module l10n_it) is minimal\n'
             '"Zeroincombenze CoA" (module l10n_it_fiscal) is a full CoA\n'
             '"Powero CoA" means manual CoA\n',
        default=lambda self: self._set_coa_2_use())
    distro = fields.Selection(
        [('odoo_ce', 'Odoo/OCA CE'),
         ('odoo_ee', 'Odoo EE'),
         ('zero', 'Zeroincombenze + OCA'),
         ('powerp', 'Powerp + OCA')],
        'Odoo Ditribution/Edition',
        default=lambda self: self._set_distro())
    set_seq = fields.Boolean('Set line sequence')
    load_sp = fields.Boolean(
        'Activate Split Payment',
        default=lambda self: self._set_flag('load_sp'))
    load_rc = fields.Boolean(
        'Activate Reverse Charge',
        default=lambda self: self._set_flag('load_rc'))
    load_wh = fields.Boolean(
        'Activate Withholding Tax',
        default=lambda self: self._set_flag('load_wh'))
    load_li = fields.Boolean(
        'Activate Lettera di Intento',
        default=lambda self: self._set_flag('load_li'))
    load_vat = fields.Boolean(
        'Activate VAT modules',
        default=lambda self: self._set_flag('load_vat'))
    load_fiscal = fields.Boolean(
        'Activate fiscal modules',
        default=lambda self: self._set_flag('load_fiscal'))
    load_conai = fields.Boolean(
        'Activate Conai',
        default=False)
    load_sct = fields.Boolean(
        'Activate Sepa Credit Transfer',
        default=False)
    load_sdd = fields.Boolean(
        'Activate Sepa Direct Debit',
        default=False)
    load_riba = fields.Boolean(
        'Activate RiBA',
        default=False)
    load_coa = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load Chart of Account')
    load_image = fields.Boolean('Load record images', default=True)
    load_partner = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load partners')
    load_product = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load products')
    load_sale_order = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load sale orders')
    load_purchase_order = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load purchase orders')
    load_invoice = fields.Selection(
        [('add', 'Add only new records'),
         ('all', 'Add or rewrite all records'),
         ('dup', 'Add/duplicate all records'),
         ], 'Load invoices')
    ctr_rec_new = fields.Integer('New record inserted', readonly=True)
    ctr_rec_upd = fields.Integer('Record updated', readonly=True)
    ctr_rec_del = fields.Integer('Record deleted', readonly=True)
    status_mesg = fields.Text('Installation status',
                              readonly=True)

    @api.onchange('load_sp', 'load_rc', 'load_wh',
                  'load_li', 'load_conai', 'load_sct', 'load_sdd')
    def flag_load_change(self):
        for item in ('load_sp', 'load_rc', 'load_wh',
                  'load_li', 'load_conai', 'load_sct', 'load_sdd'):
            if not getattr(self._origin, item) and getattr(self, item):
                self.force_test_values = True

    @api.onchange('coa')
    def _onchange_coa(self):
        self.distro = self._set_distro()

    @api.onchange('distro')
    def _onchange_distro(self):
        if self.distro == 'powerp' and release.version_info[0] < 12:
            self.distro = 'zero'

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
                         ('name', 'like', r'%%\%s' % tok),
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
                         ('name', 'like', r'%%\%s' % tok),
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

    @api.model
    def name_by_distro(self, module):
        return MODULES_BY_DISTRO.get(module, module)

    @api.model
    def get_module_list(self, scope=None):
        modules = [scope] if scope else MODULES_NEEDED.keys()
        modules_2_install = []
        modules_2_remove = []
        for item in modules:
            if scope or item == '*' or getattr(self, item):
                if isinstance(MODULES_NEEDED[item], (list, tuple)):
                    modules_2_install += MODULES_NEEDED[item]
                elif isinstance(MODULES_NEEDED[item], dict):
                    if getattr(self, item) and MODULES_NEEDED[item].get('*'):
                        modules_2_install += MODULES_NEEDED[item]['*']
                    if MODULES_NEEDED[item].get(getattr(self, item)):
                        modules_2_install += MODULES_NEEDED[item][getattr(
                            self, item)]
        if not any([x for x in modules_2_install if x in COA_MODULES]):
            modules_2_install.append('l10n_it_fiscal')
        module_list = []
        for module in modules_2_install:
            distro_module = self.name_by_distro(module)
            if distro_module != module:
                if self.distro == 'powerp':
                    modules_2_remove.append(module)
                    module_list.append(distro_module)
                else:
                    modules_2_remove.append(distro_module)
                    module_list.append(module)
            else:
                module_list.append(module)
        modules_2_install = [self.translate('', module, ttype='module')
                       for module in module_list]
        return list(set(modules_2_install)), list(set(modules_2_remove))

    @api.model
    def install_modules(self, modules_to_install, modules_to_remove,
                        no_clear_cache=None):
        modules_model = self.env['ir.module.module']
        to_install_modules = modules_model
        modules_found = []
        modules_2_test = []
        for module in modules_model.search(
                [('name', 'in', modules_to_install)]):
            if not module:
                # Module of 10.0 does not exist
                continue
            elif module.state == 'uninstalled':
                if len(modules_to_install) != 1 and module.name in COA_MODULES:
                    # CoA modules must be installed before others
                    self.install_modules([module.name], [], no_clear_cache=True)
                    continue
                to_install_modules += module
                self.status_mesg += 'Module "%s" installed\n' % module.name
                modules_found.append(module.name)
                modules_2_test.append(module.name)
                self.ctr_rec_new += 1
            elif module.state == 'uninstallable':
                self.status_mesg += \
                    'Module "%s" cannot be installed!\n' % module.name
                modules_found.append(module.name)
            elif module.state == 'installed':
                self.status_mesg += \
                    'Module "%s" was already installed\n' % module.name
                modules_found.append(module.name)
        for module in list(set(modules_to_install) - set(modules_found)):
            if module:
                self.status_mesg += \
                    'Module "%s" not found in this database!\n' % module
        max_time_to_wait = 2
        if to_install_modules:
            to_install_modules.button_immediate_install()
            max_time_to_wait += len(to_install_modules)
        found_uninstalled = True
        while max_time_to_wait > 0 and found_uninstalled:
            time.sleep(1)
            max_time_to_wait -= 1
            found_uninstalled = False
            for module in modules_model.search(
                    [('name', 'in', modules_2_test),
                     ('state', '!=', 'installed')]):
                found_uninstalled = module
                break
        if found_uninstalled:
            raise UserError(
                'Module %s not installed!' % found_uninstalled.name)
        if modules_to_remove:
            if to_install_modules:
                time.sleep(2)
            to_remove_modules = modules_model
            for module in modules_model.search(
                    [('name', 'in', modules_to_remove),
                     ('state', '=', 'installed')]):
                to_remove_modules += module
                self.status_mesg += 'Module "%s" uninstalled\n' % module.name
                self.ctr_rec_upd += 1
            to_remove_modules.module_uninstall()
            max_time_to_wait += len(to_remove_modules)
            while max_time_to_wait > 0:
                time.sleep(1)
                max_time_to_wait -= 1
                if not modules_model.search(
                        [('name', 'in', modules_to_remove),
                         ('state', '=', 'installed')]):
                    break
        if ((not to_install_modules and modules_to_remove) or
                (to_install_modules and not modules_to_remove)):
            time.sleep(2)
        else:
            time.sleep(1)
        if not no_clear_cache and to_install_modules and modules_to_remove:
            # We need to invalidate cache to load model of installed modules
            # self.env.invalidate_all()
            self.invalidate_cache()
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
        if model in self.env:
            self.STRUCT[model] = self.env[model].fields_get()
        else:
            raise UserError(
                'Model %s not found!' % model)

    def bind_record(self, model, vals, company_id,
                    field=None, parent_id=None, parent_name=None, retrec=None):
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
                return recs[0] if retrec else recs[0].id
        return False

    @api.model
    def bind_fields(self, model, vals, company_id,
                    parent_id=None, parent_model=None, mode=None):
        self.setup_model_structure(model)
        if (self.load_image and vals.get('id') and
                'image' in self.STRUCT[model]):
            filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(
                vals['id'])
            if filename:
                vals['image'] = z0bug_odoo_lib.Z0bugOdoo().get_image(
                    vals['id'])
        if mode == 'dup':
            del vals['id']
        parent_name = ''
        for field in vals.copy().keys():
            if vals[field] is None or vals[field] in ('None', r'\N'):
                del vals[field]
                continue
            if self.translate(model, field, ttype='valuetnl', fld_name=field):
                vals[field] = self.translate(
                    model, vals[field], ttype='value', fld_name=field)
            attrs = self.STRUCT[model].get(field, {})
            if not attrs:
                del vals[field]
                mesg = 'Model "%s" w/o field "%s"!!!\n' % (model, field)
                if mesg not in self.status_mesg:
                    self.status_mesg += mesg
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
                    else:
                        del vals[field]
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
            if (model == 'res.partner' and
                    parent_id and
                    release.version_info[0] > 10 and
                    not vals.get('name')):
                vals['name'] = self.env[model].browse(parent_id).name
            if mode != 'dup':
                rec = self.bind_record(
                    model, vals, company_id,
                    parent_id=parent_id, parent_name=parent_name, retrec=True)
                if rec:
                    vals['id'] = rec.id
                elif 'id' in vals:
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
                elif attrs['type'] in ('one2many', 'many2many'):
                    if rec[field]:
                        value = [(6, 0, [x.id for x in rec[field]])]
                        if value == vals[field]:
                            del vals[field]
                elif attrs['type'] == 'boolean':
                    if isinstance(
                            vals[field], bool) and vals[field] == rec[field]:
                        del vals[field]
                    elif os0.str2bool(vals[field], False) == rec[field]:
                        del vals[field]
                elif (isinstance(vals[field], float) and
                      ((not rec[field] and not vals[field]) or
                       (round(vals[field], 3) == round(rec[field]), 3))):
                    del vals[field]
                elif (isinstance(vals[field],
                                 (basestring, int, date, datetime)) and
                      ((vals[field] == rec[field]) or
                       (not rec[field] and not vals[field]))):
                    del vals[field]
        return vals

    @api.model
    def write_diff(self, model, xid, vals, xref,
                   parent_id=None, parent_model=None):
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
            if not parent_model and not parent_id:
                mesg = '- Model "%s" updated "%s"\n' % (model, xref)
                self.status_mesg += mesg

    @api.model
    def store_xref(self, xref, model, company_id,
                   parent_id=None, parent_model=None, seq=None, mode=None):
        if mode == 'dup' and xref in UNIQUE_REFS:
            mode = 'all'
        if parent_id and parent_model:
            xid = False
        else:
            xid = self.env_ref(xref, company_id=company_id, model=model)
        if not xid or mode in ('all', 'dup'):
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
            if 'sequence' in self.STRUCT[model] and seq:
                vals['sequence'] = seq
            vals, parent_name = self.bind_fields(
                model, vals, company_id,
                parent_id=parent_id, parent_model=parent_model, mode=mode)
            if mode == 'dup':
                xid = False
            else:
                if vals.get('id') and isinstance(vals['id'], int):
                    xid = vals['id']
                if not xid:
                    xid = self.bind_record(model, vals, company_id,
                                           parent_id=parent_id,
                                           parent_name=parent_name)
            if xid:
                self.write_diff(model, xid, vals, xref,
                                parent_id=parent_id, parent_model=parent_model)
            else:
                if 'id' in vals:
                    del vals['id']
                try:
                    xid = self.env[model].create(vals).id
                    self.ctr_rec_new += 1
                    if not parent_model and not parent_id:
                        mesg = '- Model "%s" added "%s"\n' % (
                            model, xref)
                        self.status_mesg += mesg
                except BaseException as e:
                    self._cr.rollback()  # pylint: disable=invalid-commit
                    self.status_mesg += ('*** Error %s!!!\n' % e)
                    xid = False
                    raise UserError(self.status_mesg)
            if xid and (not parent_id or not parent_model):
                self.add_xref(xref, model, xid)
        return xid

    @api.model
    def do_workflow(self, model, rec_id, FCT):
        if model in FCT:
            stated = []
            rec = self.env[model].browse(rec_id)
            while rec.state in FCT[model]:
                old_state = rec.state
                if old_state in stated:
                    break
                stated.append(old_state)
                for action in FCT[model][old_state]:
                    if hasattr(self.env[model], action):
                        getattr(rec, action)()
                        if not action.startswith('action'):
                            rec.write({})
                rec = self.env[model].browse(rec_id)

    @api.model
    def do_draft(self, model, rec_id):
        self.do_workflow(model, rec_id, DRAFT_FCT)

    @api.model
    def do_commit(self, model, rec_id):
        self._cr.commit()  # pylint: disable=invalid-commit
        self.do_workflow(model, rec_id, COMMIT_FCT)

    @api.model
    def make_model(self, model, mode=None, model2=None, cantdup=None):
        if cantdup and mode == 'dup':
            mode = 'all'
        self.setup_model_structure(model)
        company_id = False
        if 'company_id' in self.STRUCT[model]:
            company_id = self.company_id.id
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
                                mode=mode, parent_id=parent_id,
                                parent_model=model, seq=seq)
            else:
                if seq:
                    # Previous write was a detail record
                    self.do_commit(model, parent_id)
                parent_id = self.store_xref(xref, model, company_id, mode=mode)
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
    def mk_account_account(self, company_id, mode=None):
        model = 'account.account'
        self.setup_model_structure(model)
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model)
        for xref in sorted(xrefs):
            # Prima i mastri
            if len(xref) == 12:
                self.store_xref(xref, model, company_id, mode=mode)
        for xref in xrefs:
            # poi i capoconti
            if len(xref) == 13:
                self.store_xref(xref, model, company_id, mode=mode)
        for xref in xrefs:
            # infine i sottoconti
            if len(xref) > 13:
                self.store_xref(xref, model, company_id, mode=mode)

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
    def set_user_preference(self):
        self.env.user.write({
            'lang': self.lang,
            'tz': self.tz,
        })

    @api.model
    def enable_cancel_journal(self):
        journal_model = self.env['account.journal']
        for rec in journal_model.search([('update_posted', '=', False)]):
            rec.write({'update_posted': True})

    @api.model
    def load_language(self, iso=None):
        iso = iso or 'en_US'
        lang_model = self.env['res.lang']
        languages = lang_model.search([('code', '=', iso)])
        if not languages:
            languages = lang_model.search([('code', '=', iso),
                                           ('active', '=', False)])
            if languages:
                languages.write({'active': True})
        if not languages:
            vals = {
                'lang': iso,
                'overwrite': True
            }
            self.env['base.language.install'].create(vals).lang_install()
            self.status_mesg += 'Language "%s" installed\n' % iso
        if iso != 'en_US':
            vals = {'lang': iso}
            self.env['base.update.translations'].create(vals).act_update()
            self.status_mesg += 'Update translation "%s"\n' % iso

    def make_test_environment(self):
        # Block 0: TODO> Separate function
        self.ctr_rec_new = 0
        self.ctr_rec_upd = 0
        self.ctr_rec_del = 0
        self.status_mesg = ''
        self.load_language()
        if self.lang and self.lang != self.env.user.lang:
            self.load_language(iso=self.lang)
        self.set_user_preference()
        modules_to_install, modules_to_remove = self.get_module_list()
        self.install_modules(modules_to_install, modules_to_remove)
        self.state = '1'

        # Block 1: TODO> Separate function
        if self.new_company:
            self.create_company()
        elif not self.test_company_id:
            self.set_company_to_test(self.company_id)
        if self.load_coa and self.coa == 'powerp':
            self.mk_account_account(
                self.company_id.id, mode=self.load_coa, cantdup=True)
            self.make_model('account.tax', mode=self.load_coa, cantdup=True)
        if self.load_coa:
            self.make_model(
                'decimal.precision', mode=self.load_coa, cantdup=True)
            self.make_model('account.fiscal.position', mode=self.load_coa)
            self.make_model(
                'date.range.type', mode=self.load_coa, cantdup=True)
            self.make_model(
                'date.range', mode=self.load_coa, cantdup=True)
            self.make_model('account.fiscal.year', mode=self.load_coa)
            self.make_model('account.payment.term', mode=self.load_coa,
                            model2='account.payment.term.line')
            self.make_model(
                'account.journal', mode=self.load_coa, cantdup=True)
            self.enable_cancel_journal()
            if self.load_wh:
                self.make_model('withholding.tax', mode=self.load_coa,
                                model2='withholding.tax.rate', cantdup=True)
        if self.load_partner:
            self.make_model('res.partner', mode=self.load_partner)
            self.make_model(
                'res.partner.bank', mode=self.load_partner, cantdup=True)
        if self.load_product:
            self.make_model(
                'product.template', mode=self.load_product, cantdup=True)
            self.make_model(
                'product.product', mode=self.load_product, cantdup=True)
        self.state = '2'

        # Block 2: TODO> Separate function
        if self.load_sale_order:
            self.make_model('sale.order', mode=self.load_sale_order,
                            model2='sale.order.line')
        if self.load_purchase_order:
            self.make_model('purchase.order', mode=self.load_purchase_order,
                            model2='purchase.order.line')
        if self.load_invoice:
            self.make_model('account.invoice', mode=self.load_invoice,
                            model2='account.invoice.line')
        self.status_mesg += 'Data (re)loaded.\n'
        self.state = '9'

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
