#
# Copyright 2019-21 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# from past.builtins import basestring
# from builtins import int
# import os
from datetime import datetime
# import time
# import re
# import pytz
import itertools

from odoo import api, fields, models
# from odoo.exceptions import UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''

from z0bug_odoo import z0bug_odoo_lib
# from os0 import os0
# from clodoo import transodoo
import python_plus


SOURCE_HEADER = """\"\"\"
Tests are based on test environment created by module mk_test_env in repository
https://github.com/zeroincombenze/zerobug-test

Each model is declared by a dictionary which name should be "TEST_model",
where model is the upercase model name with dot replaced by '_'
i.e.: res_partner -> TEST_RES_PARTNER

Every record is declared in the model dictionary by a key which is the external
reference used to retrieve the record.
i.e.:
TEST_RES_PARTNER = {
    'z0bug.partner1': {
        'name': 'Alpha',
        'street': '1, First Avenue',
        ...
    }
}

The magic dictionary TEST_SETUP contains data to load at test setup.
TEST_SETUP = {
    'res.partner': TEST_RES_PARTNER,
    ...
}

In setup() function, the following code
    self.setup_records(lang='it_IT')
creates all record declared by above data; lang is an optional parameter.

Final notes:
* Many2one value must be declared as external identifier
* Written on %s by mk_test_env %s
\"\"\"
import logging
from odoo.tests import common

_logger = logging.getLogger(__name__)

"""
SOURCE_BODY = """
TNL_RECORDS = {
    'product.product': {
        # 'type': ['product', 'consu'],
    },
    'product.template': {
        # 'type': ['product', 'consu'],
    },
}


class TestAccountMove(common.TransactionCase):

    # --------------------------------------- #
    # Common code: may be share among modules #
    # --------------------------------------- #

    def simulate_xref(self, xref, raise_if_not_found=None,
                      model=None, by=None, company=None, case=None):
        \"\"\"Simulate External Reference
        This function simulates self.env.ref() searching for model record.
        Ordinary xref is formatted as "MODULE.NAME"; when MODULE = "external"
        this function is called.
        Record is searched by <by> parameter, default is 'code' or 'name';
        id NAME is formatted as "FIELD=VALUE", FIELD value is assigned to <by>
        If company is supplied, it is added in search domain;

        Args:
            xref (str): external reference
            raise_if_not_found (bool): raise exception if xref not found or
                                       if more records found
            model (str): external reference model
            by (str): default field to search object record,
            company (obj): default company
            case: apply for uppercase or lowercase

        Returns:
            obj: the model record
        \"\"\"
        if model not in self.env:
            if raise_if_not_found:
                raise ValueError('Model %%s not found in the system' %% model)
            return False
        _fields = self.env[model].fields_get()
        if not by:
            if model in self.by:
                by = self.by[model]
            else:
                by = 'code' if 'code' in _fields else 'name'
        module, name = xref.split('.', 1)
        if '=' in name:
            by, name = name.split('=', 1)
        if case == 'upper':
            name = name.upper()
        elif case == 'lower':
            name = name.lower()
        domain = [(by, '=', name)]
        if (model not in ('product.product',
                          'product.template',
                          'res.partner',
                          'res.users') and
                company and 'company_id' in _fields):
            domain.append(('company_id', '=', company.id))
        objs = self.env[model].search(domain)
        if len(objs) == 1:
            return objs[0]
        if raise_if_not_found:
            raise ValueError('External ID not found in the system: %%s' %% xref)
        return False

    def env_ref(self, xref, raise_if_not_found=None,
                model=None, by=None, company=None, case=None):
        \"\"\"Get External Reference
        This function is like self.env.ref(); if xref does not exist and
        xref prefix is 'external.', engage simulate_xref

        Args:
            xref (str): external reference, format is "module.name"
            raise_if_not_found (bool): raise exception if xref not found
            model (str): external ref. model; required for "external." prefix
            by (str): field to search object record, default is 'code' or 'name'
            company (obj): default company

        Returns:
            obj: the model record
        \"\"\"
        if xref is False or xref is None:
            return xref
        obj = self.env.ref(xref, raise_if_not_found=raise_if_not_found)
        if not obj:
            module, name = xref.split('.', 1)
            if module == 'external':
                return self.simulate_xref(xref,
                                          model=model,
                                          by=by,
                                          company=company,
                                          case=case)
        return obj

    def add_xref(self, xref, model, xid):
        \"\"\"Add external reference that will be used in next tests.
        If xref exist, result ID will be upgraded\"\"\"
        module, name = xref.split('.', 1)
        if module == 'external':
            return False
        ir_model = self.env['ir.model.data']
        vals = {
            'module': module,
            'name': name,
            'model': model,
            'res_id': xid,
        }
        xrefs = ir_model.search([('module', '=', module),
                                 ('name', '=', name)])
        if not xrefs:
            return ir_model.create(vals)
        xrefs[0].write(vals)
        return xrefs[0]

    def get_values(self, model, values, by=None, company=None, case=None):
        \"\"\"Load data values and set them in a dictionary for create function
        * Not existent fields are ignored
        * Many2one field are filled with current record ID
        \"\"\"
        _fields = self.env[model].fields_get()
        vals = {}
        if model in TNL_RECORDS:
            for item in TNL_RECORDS[model].keys():
                if item in values:
                    (old, new) = TNL_RECORDS[model][item]
                    if values[item] == old:
                        values[item] = new
        for item in values.keys():
            if item not in _fields:
                continue
            if item == 'company_id' and not values[item]:
                vals[item] = company.id
            elif _fields[item]['type'] == 'many2one':
                res = self.env_ref(
                    values[item],
                    model=_fields[item]['relation'],
                    by=by,
                    company=company,
                    case=case,
                )
                if res:
                    vals[item] = res.id
            elif (_fields[item]['type'] == 'many2many' and
                  '.' in values[item] and
                  ' ' not in values[item]):
                res = self.env_ref(
                    values[item],
                    model=_fields[item]['relation'],
                    by=by,
                    company=company,
                    case=case,
                )
                if res:
                    vals[item] = [(6, 0, [res.id])]
            elif values[item] is not None:
                vals[item] = values[item]
        return vals

    def model_create(self, model, values, xref=None):
        \"\"\"Create a test record and set external ID to next tests\"\"\"
        res = self.env[model].create(values)
        if xref and ' ' not in xref:
            self.add_xref(xref, model, res.id)
        return res

    def model_browse(self, model, xid, company=None, by=None,
                     raise_if_not_found=True):
        \"\"\"Browse a record by external ID\"\"\"
        res = self.env_ref(
            xid,
            model=model,
            company=company,
            by=by,
        )
        if res:
            return res
        return self.env[model]

    def model_make(self, model, values, xref, company=None, by=None):
        \"\"\"Create or write a test record and set external ID to next tests\"\"\"
        res = self.model_browse(model,
                                xref,
                                company=company,
                                by=by,
                                raise_if_not_found=False)
        if res:
            res.write(values)
            return res
        return self.model_create(model, values, xref=xref)

    def default_company(self):
        return self.env.user.company_id

    def set_locale(self, locale_name, raise_if_not_found=True):
        modules_model = self.env['ir.module.module']
        modules = modules_model.search([('name', '=', locale_name)])
        if modules and modules[0].state != 'uninstalled':
            modules = []
        if modules:
            modules.button_immediate_install()
            self.env['account.chart.template'].try_loading_for_current_company(
                locale_name
            )
        else:
            if raise_if_not_found:
                raise ValueError(
                    'Module %%s not found in the system' %% locale_name)

    def install_language(self, iso, overwrite=None, force_translation=None):
        iso = iso or 'en_US'
        overwrite = overwrite or False
        load = False
        lang_model = self.env['res.lang']
        languages = lang_model.search([('code', '=', iso)])
        if not languages:
            languages = lang_model.search([('code', '=', iso),
                                           ('active', '=', False)])
            if languages:
                languages.write({'active': True})
                load = True
        if not languages or load:
            vals = {
                'lang': iso,
                'overwrite': overwrite,
            }
            self.env['base.language.install'].create(vals).lang_install()
        if force_translation:
            vals = {'lang': iso}
            self.env['base.update.translations'].create(vals).act_update()

    def setup_records(self, lang=None, locale=None, company=None,
                      save_as_demo=None):
        \"\"\"Create all record from declared data. See above doc

        Args:
            lang (str): install & load specific language
            locale (str): install locale module with CoA; i.e l10n_it
            company (obj): declare default company for tests
            save_as_demo (bool): commit all test data as they are demo data
            Warning: usa save_as_demo carefully; is used in multiple tests,
            like in travis this option can be cause to failue of tests
            This option can be used in local tests with "run_odoo_debug -T"

        Returns:
            None
        \"\"\"

        def iter_data(model, model_data, company):
            for item in model_data.keys():
                if isinstance(model_data[item], str):
                    continue
                vals = self.get_values(
                    model,
                    model_data[item],
                    company=company)
                res = self.model_make(
                    model, vals, item,
                    company=company,
                    by=by)
                if model == 'product.template':
                    model2 = 'product.product'
                    vals = self.get_values(
                        model2,
                        model_data[item],
                        company=company)
                    vals['product_tmpl_id'] = res.id
                    self.model_make(
                        model2, vals, item.replace('template', 'product'),
                        company=company,
                        by=by)

        self.save_as_demo = save_as_demo or False
        if locale:
            self.set_locale(locale)
        if lang:
            self.install_language('it_IT')
        if not self.env['ir.module.module'].search(
                [('name', '=', 'stock'), ('state', '=', 'installed')]):
            TNL_RECORDS['product.product']['type'] = ['product', 'consu']
            TNL_RECORDS['product.template']['type'] = ['product', 'consu']
        self.by = {}
        for model, model_data in TEST_SETUP.items():
            by = model_data.get('by')
            if by:
                self.by[model] = by
        company = company or self.default_company()
        import pdb; pdb.set_trace()
        for model, model_data in TEST_SETUP.items():
            by = model_data.get('by')
            iter_data(model, model_data, company)

    # ------------------ #
    # Specific test code #
    # ------------------ #
    def setUp(self):
        super().setUp()
        self.setup_records(lang='it_IT')

    def tearDown(self):
        if self.save_as_demo:
            self.env.cr.commit()               # pylint: disable=invalid-commit

    def test_something(self):
        # Here an example of code you should insert to test
        for item in %(title)s:
            model = '%(model)s'
            _logger.debug(
                "... Testing %%s[%%s]" %% (model, item)
            )
            vals = self.get_values(
                model,
                %(title)s[item])
            rec = self.model_make(model, vals, item)

            model = '%(model)s.line'
            for line in %(title)s_LINE.values():
                vals = self.get_values(model, line)
            vals['parent_id'] = rec.id
            self.model_make(model, vals, False)
            # inv.compute_taxes()
"""


class WizardMkTestPyfile(models.TransientModel):
    _name = "wizard.mk.test.pyfile"
    _description = "Create python source test file"

    xref_ids = fields.Many2many(
        'ir.model.data',
        string='External references')
    source = fields.Text('Source code')
    oca_coding = fields.Boolean('OCA coding', default=True)
    product_variant = fields.Boolean('Add product variant', default=False)
    max_child_records = fields.Integer('Max child records', default=0)

    OCA_TNL = {
        'z0bug.coa_260010': 'external.2601',
        'z0bug.coa_153010': 'external.1601',
        'z0bug.coa_510000': 'external.3112',
        'z0bug.coa_510100': 'external.3101',
        'z0bug.coa_610100': 'external.4101',
        'external.FAT|FATT|INV': 'external.INV',
        'external.ACQ|FATTU|BILL': 'external.BILL',
        'z0bug.tax_22v': 'external.22v',
        'z0bug.tax_22a': 'external.22a',
        'z0bug.partner_mycompany': 'base.main_partner',
    }
    MODEL_BY = {
        'account.tax': 'description',
        'product.template': 'default_code',
        'product.product': 'default_code',
    }
    HIDDEN_FIELDS = {
        'account.account': ['group_id'],
        'account.fiscal.position': ['sequence'],
        'account.journal': ['sequence', 'group_inv_lines_mode'],
        'account.tax': ['sequence'],
        'account.invoice.line': ['invoice_id'],
        'product.template': ['categ_id', 'route_ids'],
        'product.product': ['categ_id', 'route_ids'],
    }

    def get_xref_obj(self, xref):
        ir_model = self.env['ir.model.data']
        module, name = xref.split('.', 1)
        xrefs = ir_model.search([('module', '=', module),
                                 ('name', '=', name)])
        if not xrefs:
            return False
        return xrefs[0]

    def get_test_values(self, model, xref):
        try:
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model, xref)
        except BaseException:
            vals = None
        return vals

    def get_child_model(self, model):
        model_line = '%s.line' % model
        if model_line not in self.env:
            model_line = False
        return model_line

    def push_xref(self, xref, model):
        self.model_of_xref[xref] = model
        module, name = xref.split('.', 1)
        if module not in self.modules_to_declare:
            return
        vals = self.get_test_values(model, xref)
        if not vals:
            return
        if xref not in self.sound_xrefs:
            self.sound_xrefs.append(xref)
        if model not in self.sound_models:
            self.sound_models.append(model)
        if model not in self.struct:
            self.struct[model] = self.env[model].fields_get()
        for field in vals.keys():
            if (field == 'id' or
                    field not in self.struct[model] or
                    vals[field] is None):
                continue
            if self.struct[model][field].get('relation'):
                if vals[field] not in self.dep_xrefs:
                    self.dep_xrefs.append(vals[field])
                    self.push_xref(vals[field],
                                   self.struct[model][field]['relation'])

    def push_child_xref(self, xref, model, model_child):
        if model not in self.struct:
            self.struct[model] = self.env[model].fields_get()
        if model_child not in self.struct:
            self.struct[model_child] = self.env[model_child].fields_get()
        if xref not in self.top_child_xrefs:
            self.top_child_xrefs[xref] = []
        xrefs = z0bug_odoo_lib.Z0bugOdoo().get_test_xrefs(model_child)
        record_ctr = 0
        for xref_child in xrefs:
            if self.max_child_records and record_ctr >= self.max_child_records:
                break
            self.model_of_xref[xref_child] = model_child
            vals = self.get_test_values(model_child, xref_child)
            for field in vals.keys():
                if (field == 'id' or
                        field not in self.struct[model_child] or
                        vals[field] is None):
                    continue
                if (self.struct[model_child][field]['type'] == 'many2one' and
                        self.struct[model_child][field].get('relation') and
                        (self.struct[model_child][field][
                             'relation'] == model and
                         vals[field] == xref)):
                    self.top_child_xrefs[xref].append(xref_child)
                    record_ctr += 1
        for xref_child in self.top_child_xrefs[xref]:
            self.push_xref(xref_child, model_child)

    def write_source_model(self, model, xrefs, exclude_xref=None):
        if not self.product_variant and model == 'product.product':
            return '', False, ''
        exclude_xref = exclude_xref or []
        xrefs = xrefs or self.sound_xrefs
        valid = False
        title = "TEST_%s" % model.replace('.', '_').upper()
        source = "%s = {\n" % title
        if model in self.MODEL_BY:
            source += "    'by': '%s',\n" % self.MODEL_BY[model]
        toc = ''
        for xref in xrefs:
            if xref in exclude_xref or self.model_of_xref[xref] != model:
                continue
            if self.oca_coding:
                oca_xref = self.OCA_TNL.get(xref, xref)
            else:
                oca_xref = xref
            source += "    '%s': {\n" % oca_xref
            valid = True
            toc = "    '%s': %s,\n" % (model, title)
            vals = self.get_test_values(model, xref)
            if model in self.HIDDEN_FIELDS:
                for field in self.HIDDEN_FIELDS[model]:
                    if field in vals:
                        del vals[field]
            if oca_xref != xref:
                module, oca_name = oca_xref.split('.', 1)
                if model == 'account.account':
                    vals['code'] = oca_name
                elif model == 'account.tax':
                    vals['description'] = oca_name
                elif model == 'account.journal':
                    vals['code'] = oca_name
            for field in vals.keys():
                if (field == 'id' or
                        field not in self.struct[model] or
                        vals[field] is None):
                    continue
                if self.struct[model][field]['type'] in ('date', 'datetime'):
                    vals[field] = python_plus.compute_date(vals[field])
                if self.oca_coding:
                    vals[field] = self.OCA_TNL.get(vals[field], vals[field])
                if self.struct[model][field]['type'] in ('integer',
                                                         'float',
                                                         'monetary'):
                    source += "        '%s': %s,\n" % (field, vals[field])
                elif self.struct[model][field]['type'] == 'boolean':
                    source += "        '%s': %s,\n" % (
                        field, 'True' if vals[field] else 'False')
                else:
                    source += "        '%s': '%s',\n" % (field, vals[field])
            source += "    },\n"
        source += "}\n"
        return source, valid, toc

    def make_test_pyfile(self):
        self.modules_to_declare = ('z0bug', 'external', 'l10n_it')
        self.model_of_xref = {}
        self.top_xrefs = []
        self.top_child_xrefs = {}
        self.sound_xrefs = []
        self.sound_models = []
        self.struct = {}
        self.dep_xrefs = []

        # Phase 1:
        # find & store all xrefs child or depending on required xrefs
        for xref_obj in self.xref_ids:
            xref = '%s.%s' % (xref_obj.module, xref_obj.name)
            if xref in self.top_xrefs:
                continue
            self.top_xrefs.append(xref)
            model = xref_obj.model
            model_child = self.get_child_model(model)
            if model_child:
                self.push_child_xref(xref, model, model_child)
            self.push_xref(xref, model)

        # Phase 2:
        # For every model depending on required model, write field data
        self.source = SOURCE_HEADER % (
            datetime.today(),
            self.env['ir.module.module'].search(
                [('name', '=', 'mk_test_env')]).latest_version)
        test_setup = 'TEST_SETUP = {\n'
        for model in sorted(self.sound_models):
            source, valid, toc = self.write_source_model(
                model, self.sound_xrefs,
                exclude_xref=self.top_xrefs + list(
                    itertools.chain(*self.top_child_xrefs.values())))
            if valid:
                self.source += source
                test_setup += toc
        test_setup += "}\n"
        self.source += test_setup

        # Phase 3:
        # For every model child of required model, write field data
        self.source += '\n'
        sound_model_child = []
        for xref_obj in self.xref_ids:
            xref = '%s.%s' % (xref_obj.module, xref_obj.name)
            model = xref_obj.model
            model_child = self.get_child_model(model)
            if model_child and model_child not in sound_model_child:
                source, valid, toc = self.write_source_model(
                    model_child, self.top_child_xrefs[xref])
                if valid:
                    self.source += source
                sound_model_child.append(model_child)

        # Phase 4:
        # Finally write required model field data
        self.source += '\n'
        sound_model = []
        for xref_obj in self.xref_ids:
            # xref = '%s.%s' % (xref_obj.module, xref_obj.name)
            model = xref_obj.model
            if model not in sound_model:
                source, valid, toc = self.write_source_model(
                    model, self.top_xrefs)
                if valid:
                    self.source += source
                    sound_model.append(model)

        self.source += SOURCE_BODY % {
            'model': model,
            'title': ("TEST_%s" % model.replace('.', '_').upper()),
        }

        return {
            'name': "Data created",
            'type': 'ir.actions.act_window',
            'res_model': 'wizard.mk.test.pyfile',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'active_id': self.id},
            'view_id': self.env.ref(
                'mk_test_env.result_mk_test_pyfile_view').id,
            'domain': [('id', '=', self.id)],
        }

    def close_window(self):
        return {'type': 'ir.actions.act_window_close'}
