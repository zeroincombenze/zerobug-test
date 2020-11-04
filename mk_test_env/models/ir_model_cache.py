# -*- coding: utf-8 -*-
#
# Copyright 2019-20 - SHS-AV s.r.l. <https://www.zeroincombenze.it/>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
import logging
from datetime import datetime, date, timedelta

from z0bug_odoo import z0bug_odoo_lib

from openerp.osv import orm
from openerp import release
# from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)
try:
    from odoo_score import odoo_score
except ImportError as err:
    _logger.error(err)
try:
    from os0 import os0
except ImportError as err:
    _logger.error(err)

SKEYS = {
    'res.country': (['code'], ['name']),
    'res.country.state': (['name', 'country_id'],
                          ['code', 'country_id'],),
    'res.partner': (['vat', 'fiscalcode', 'type'],
                    ['vat', 'name', 'type'],
                    ['fiscalcode', 'dim_name', 'type'],
                    ['rea_code'],
                    ['vat', 'dim_name', 'type'],
                    ['vat', 'type'],
                    ['dim_name', 'type'],
                    ['vat', 'fiscalcode', 'is_company'],
                    ['vat'],
                    ['name', 'is_company'],
                    ['name']),
    'res.company': (['vat'], ['name']),
    'account.account': (['code', 'company_id'],
                        ['name', 'company_id'],
                        ['dim_name', 'company_id']),
    'account.account.type': (['type'], ['name'], ['dim_name']),
    'account.tax': (['description', 'company_id'],
                    ['name', 'company_id'],
                    ['dim_name', 'company_id'],
                    ['amount', 'company_id'],),
    'account.invoice': (['number', 'company_id'], ['move_name', 'company_id']),
    'account.invoice.line': (['invoice_id', 'sequence'],
                             ['invoice_id', 'name']),
    'product.template': (['name', 'default_code'],
                         ['name', 'barcode'],
                         ['name'],
                         ['default_code'],
                         ['barcode'],
                         ['dim_name']),
    'product.product': (['name', 'default_code'],
                        ['name', 'barcode'],
                        ['name'],
                        ['default_code'],
                        ['barcode'],
                        ['dim_name']),
    'sale.order': (['name']),
    'sale.order.line': (['order_id', 'sequence'], ['order_id', 'name']),
}


class IrModelSynchroCache(orm.Model):
    _name = 'ir.model.cache'

    CACHE = odoo_score.SingletonCache()
    SYSTEM_MODEL_ROOT = [
        'base.config.',
        'base_import.',
        'base.language.',
        'base.module.',
        'base.setup.',
        'base.update.',
        'ir.actions.',
        'ir.exports.',
        'ir.model.',
        'ir.module.',
        'ir.qweb.',
        'report.',
        'res.config.',
        'web_editor.',
        'web_tour.',
        'workflow.',
    ]
    SYSTEM_MODELS = [
        '_unknown',
        'base',
        'base.config.settings',
        'base_import',
        'change.password.wizard',
        'ir.autovacuum',
        'ir.config_parameter',
        'ir.exports',
        'ir.fields.converter',
        'ir.filters',
        'ir.http',
        'ir.logging',
        'ir.model',
        'ir.needaction_mixin',
        'ir.qweb',
        'ir.rule',
        'ir.translation',
        'ir.ui.menu',
        'ir.ui.view',
        'ir.values',
        'mail.alias',
        'report',
        'res.config',
        'res.font',
        'res.request.link',
        'res.users.log',
        'web_tour',
        'workflow',
    ]
    TABLE_DEF = {
        'base': {
            # 'company_id': {'required': True},
            'create_date': {'readonly': True},
            'create_uid': {'readonly': True},
            'message_ids': {'readonly': True},
            'message_follower_ids': {'readonly': True},
            'message_last_post': {'readonly': True},
            'message_needaction': {'readonly': True},
            'message_needaction_counter': {'readonly': True},
            'message_unread': {'readonly': True},
            'message_unread_counter': {'readonly': True},
            'password': {'protect_update': 2},
            'password_crypt': {'protect_update': 2},
            'write_date': {'readonly': True},
            'write_uid': {'readonly': True},
        },
        'account.account': {
            'user_type_id': {'required': True},
            'internal_type': {'readonly': False},
        },
        'account.invoice': {
            'account_id': {'readonly': False},
            'comment': {'readonly': False},
            'date': {'readonly': False},
            'date_due': {'readonly': False},
            'date_invoice': {'readonly': False},
            'fiscal_position_id': {'readonly': False},
            'name': {'readonly': False},
            'number': {'readonly': False, 'required': False},
            'partner_id': {'readonly': False},
            'partner_shipping_id': {'readonly': False},
            'payment_term_id': {'readonly': False},
            'registration_date': {'readonly': False},
            'type': {'readonly': False},
            'user_id': {'readonly': False},
        },
        'account.payment.term': {},
        'product.category': {},
        'product.product': {
            'company_id': {'readonly': True},
        },
        'product.template': {
            'company_id': {'readonly': True},
        },
        'purchase.order': {
            'name': {'required': False},
        },
        'res.company': {
            'default_picking_type_for_package_preparation_id':
                {'readonly': True},
            'due_cost_service_id': {'readonly': True},
            'internal_transit_location_id': {'readonly': True},
            'paperformat_id': {'readonly': True},
            'of_account_end_vat_statement_interest_account_id':
                {'readonly': True},
            'of_account_end_vat_statement_interest': {'readonly': True},
            'parent_id': {'readonly': True},
            'po_lead': {'readonly': True},
            'project_time_mode_id': {'readonly': True},
            'sp_account_id': {'readonly': True},
        },
        'res.country': {},
        'res.country.state': {},
        'res.currency': {
            'rate_ids': {'protect_update': 2},
            'rounding': {'protect_update': 2},
        },
        'res.partner': {
            'company_id': {'readonly': True},
            'notify_email': {'readonly': True},
            'property_product_pricelist': {'readonly': True},
            'property_stock_customer': {'readonly': True},
            'property_stock_supplier': {'readonly': True},
            'title': {'readonly': True},
        },
        'res.partner.bank': {
            'bank_name': {'readonly': False},
        },
        'res.users': {
            'action_id': {'readonly': True},
            'category_id': {'readonly': True},
            'company_id': {'readonly': True},
            'login_date': {'readonly': True},
            'opt_out': {'readonly': True},
        },
        'sale.order': {
            'name': {'readonly': False, 'required': False},
        },
        'stock.picking.package.preparation': {
            'ddt_number': {'required': False},
        },
    }

    # -------------------------
    # General purpose functions
    # -------------------------
    def lifetime(self, lifetime):
        return self.CACHE.lifetime(self._cr.dbname, lifetime)

    def clean_cache(self, model=None, lifetime=None):
        _logger.info('> clean_cache(%d,%s)' % (
            model, (lifetime or -1)))
        cache = self.CACHE
        if lifetime:
            self.lifetime(lifetime)
        if model:
            cache.init_struct_model(self._cr.dbname, model)
        else:
            cache.init_struct(self._cr.dbname)
        return self.lifetime(0)

    def is_struct(self, model):
        return model < 'A' or model > '['

    # --------------------------
    # Model structure primitives
    # --------------------------
    def set_struct_model(self, model):
        self.CACHE.set_struct_model(self._cr.dbname, model)

    def set_struct_attr(self, attrib, value):
        self.CACHE.set_struct_model(self._cr.dbname, attrib)
        return self.CACHE.set_struct_attr(
            self._cr.dbname, attrib, value)

    def get_struct_attr(self, attrib, default=None):
        return self.CACHE.get_struct_attr(
            self._cr.dbname, attrib, default=default)

    def get_struct_model_attr(self, model, attrib, default=None):
        self.set_struct_model(model)
        return self.CACHE.get_struct_model_attr(
            self._cr.dbname, model, attrib, default=default)

    def set_struct_model_attr(self, model, attrib, value):
        self.set_struct_model(model)
        return self.CACHE.set_struct_model_attr(
            self._cr.dbname, model, attrib, value)

    def get_struct_model_field_attr(self, model, field, attrib, default=None):
        return self.CACHE.get_struct_model_field_attr(
            self._cr.dbname, model, field, attrib, default=default)

    # ----------------
    # Cache management
    # ----------------
    def bind_fields(self, model, vals, company_id,
                    parent_id=None, parent_model=None):
        self.setup_model_structure(model)
        model_model = self.pool[model]
        parent_name = ''
        for field in vals.copy():
            attrs = self.get_struct_model_attr(model, field)
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
                    recs = self.pool['ir.model.data'].browse(self._cr, self._uid,
                        self.pool['ir.model.data'].search(self._cr, self._uid,
                            [('module', '=', 'l10n_it_fiscal'),
                             ('name', 'like', r'_\%s' % tok),
                             ('model', '=', 'account.account')]))
                    for xref in recs:
                        if xref.name.endswith(tok):
                            acc = model_model.browse(
                                self._cr, self._uid, xref.res_id)
                            if acc.company_id.id == company_id:
                                vals[field] = acc.id
                                break
                if 'user_type_id' in vals:
                    if self.STRUCT[model].get('nature', {}):
                        if isinstance(vals['user_type_id'], int):
                            acc = self.pool['account.account.type'].browse(
                                self._cr, self._uid, vals['user_type_id'])
                        else:
                            acc = self.pool['account.account.type'].browse(
                                self._cr, self._uid,
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
                self.pool['ir.model.cache'].setup_model_structure(
                    attrs['relation'])
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
        if (vals.get('id') and self.wiz.load_image and
                'image' in self.STRUCT[model]):
            filename = z0bug_odoo_lib.Z0bugOdoo().get_image_filename(
                vals['id'])
            if filename:
                vals['image'] = z0bug_odoo_lib.Z0bugOdoo().get_image(
                    vals['id'])
        return vals, parent_name

    def setup_model_structure(self, model):
        """Store model structure into memory"""
        if not model or self.get_struct_model_attr(model, 'XPIRE'):
            return
        self.set_struct_model(model)
        ir_model = self.pool['ir.model.fields']
        for field in ir_model.browse(
                self._cr, self._uid, ir_model.search(
                    self._cr, self._uid, [('model', '=', model)])):
            global_def = self.TABLE_DEF.get('base', {}).get(field.name, {})
            field_def = self.TABLE_DEF.get(model, {}).get(field.name, {})
            attrs = {}
            for attr in ('required', 'readonly'):
                if attr in field_def:
                    attrs[attr] = field_def[attr]
                elif attr in global_def:
                    attrs[attr] = global_def[attr]
                elif attr == 'readonly' and (
                        field.ttype in ('binary', 'reference') or
                        (hasattr(field, 'related') and field.related and
                         not field.required)):
                    attrs['readonly'] = True
                else:
                    attrs[attr] = field[attr]
            if attrs['required']:
                attrs['readonly'] = False
            if (field.relation in self.SYSTEM_MODEL_ROOT or
                    field.relation in self.SYSTEM_MODELS):
                attrs['readonly'] = True
            self.set_struct_model_attr(
                model, field.name, {
                    'ttype': field.ttype,
                    'relation': field.relation,
                    'required': attrs['required'],
                    'readonly': attrs['readonly'],
                })
        self.CACHE.set_struct_cache(self._cr.dbname, model)

    def open(self, cr=None, uid=None, model=None):
        """Setup cache if needed, setup model cache if required and needed"""
        self._cr = cr if cr else self._cr
        self._uid = uid if uid else self._uid
        self.setup_model_structure(model)
