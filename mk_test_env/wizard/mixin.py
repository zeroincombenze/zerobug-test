#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
from past.builtins import basestring

from odoo.exceptions import UserError
try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ''

from z0bug_odoo import z0bug_odoo_lib


class BaseTestMixin():
    _name = "base.test.mixin"
    _description = "Common function for test wizards"

    def get_distro_version(self, distro):
        """Return distro + version identifier used for translation
        Args:
            distro (str): odoo distribution, mey be ('odoo', 'zero', 'librerp')
        Returns:
            distro + version identifier (str)
        """
        if distro and not distro.startswith('odoo'):
            if distro == 'powerp':
                distro_version = 'librerp%d' % release.version_info[0]
            else:
                distro_version = '%s%d' % (distro, release.version_info[0])
        else:
            distro_version = release.major_version
        return distro_version

    def get_dependencies(self, module, module_ids=None):
        """Return dependency modules of supplied module
        Args:
            module (str|obj): parent module
            module_ids (obj list|obj): list of module objects to merge
        Returns:
            set of dependency module objects
        """
        modules = module_ids or set()
        if isinstance(module, basestring):
            module = self.env['ir.module.module'].search([('name', '=', module)])
            if module:
                module = module[0]
        result = set()
        for dependency in [x.depend_id for x in module.dependencies_id]:
            result |= self.get_dependencies(dependency, module_ids=modules)
        return result | {module}

    def get_dependency_names(self, module):
        """Return dependency modules of supplied module
        Args:
            module (str|obj): parent module
        Returns:
            list of dependency module names
        """
        return [x.name for x in self.get_dependencies(module)]

    def get_test_values(self, model_name, xref):
        """Return dictionary with test value by external reference of model name
        Args:
            model_name (str): Odoo model
            xref (str): external reference (format is 'module.name')
        Returns:
            dictionary of values or None
        """
        try:
            vals = z0bug_odoo_lib.Z0bugOdoo().get_test_values(model_name, xref)
        except BaseException:
            vals = None
        return vals

    def get_fields_struct(self, model_name):
        if model_name not in self.env:
            raise UserError(
                'Model %s not found!' % model_name)
        return self.env[model_name].fields_get()

    # def map_values(self, model_name, vals):
    #     if model_name not in self.env:
    #         raise UserError(
    #             'Model %s not found!' % model_name)
    #     struct = self.env[model_name].fields_get()
