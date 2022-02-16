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
# from datetime import date, datetime
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
            if record_ctr >= self.max_child_records:
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
        self.source = ''
        test_setup = 'TEST_SETUP =  {\n'
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
