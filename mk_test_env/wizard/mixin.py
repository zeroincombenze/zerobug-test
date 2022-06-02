# -*- coding: utf-8 -*-
#
# Copyright 2019-22 SHS-AV s.r.l. <https://www.zeroincombenze.it>
#
# Contributions to development, thanks to:
# * Antonio Maria Vigliotti <antoniomaria.vigliotti@gmail.com>
#
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
#
# from past.builtins import basestring
from past.builtins import basestring

from openerp import models
from openerp.exceptions import Warning as UserError

try:
    import odoo.release as release
except ImportError:
    try:
        import openerp.release as release
    except ImportError:
        release = ""

from z0bug_odoo import z0bug_odoo_lib


class BaseTestMixin(models.AbstractModel):
    _name = "base.test.mixin"
    _description = "Common function for test wizards"

    # Default attributes for Odoo models
    TABLE_DEF = {
        "base": {
            "create_date": {"readonly": True},
            "create_uid": {"readonly": True},
            "message_channel_ids": {"readonly": True},
            "message_follower_ids": {"readonly": True},
            "message_ids": {"readonly": True},
            "message_is_follower": {"readonly": True},
            "message_last_post": {"readonly": True},
            "message_needaction": {"readonly": True},
            "message_needaction_counter": {"readonly": True},
            "message_unread": {"readonly": True},
            "message_unread_counter": {"readonly": True},
            "password": {"protect_update": 2},
            "password_crypt": {"protect_update": 2},
            "write_date": {"readonly": True},
            "write_uid": {"readonly": True},
        },
        "account.account": {
            "user_type_id": {"required": True},
            "internal_type": {"readonly": False},
        },
        "account.invoice": {
            "account_id": {"readonly": False},
            "comment": {"readonly": False},
            "date": {"readonly": False},
            "date_due": {"readonly": False},
            "date_invoice": {"readonly": False},
            "fiscal_position_id": {"readonly": False},
            "name": {"readonly": False},
            "number": {"readonly": False, "required": False},
            "partner_id": {"readonly": False},
            "partner_shipping_id": {"readonly": False},
            "payment_term_id": {"readonly": False},
            "registration_date": {"readonly": False},
            "type": {"readonly": False},
            "user_id": {"readonly": False},
        },
        "account.payment.term": {},
        "ir.sequence": {"number_next_actual": {"protect_update": 4}},
        "product.category": {},
        "product.product": {
            "company_id": {"readonly": True},
        },
        "product.template": {
            "company_id": {"readonly": True},
        },
        "purchase.order": {
            "name": {"required": False},
        },
        "res.company": {
            "default_picking_type_for_package_preparation_id": {"readonly": True},
            "due_cost_service_id": {"readonly": True},
            "internal_transit_location_id": {"readonly": True},
            "paperformat_id": {"readonly": True},
            "of_account_end_vat_statement_interest_account_id": {"readonly": True},
            "of_account_end_vat_statement_interest": {"readonly": True},
            "parent_id": {"readonly": True},
            "po_lead": {"readonly": True},
            "project_time_mode_id": {"readonly": True},
            "sp_account_id": {"readonly": True},
        },
        "res.country": {
            "name": {"protect_update": 2},
        },
        "res.country.state": {"name": {"protect_update": 2}},
        "res.currency": {
            "rate_ids": {"protect_update": 2},
            "rounding": {"protect_update": 2},
        },
        "res.partner": {
            "company_id": {"readonly": True},
            "notify_email": {"readonly": True},
            "property_product_pricelist": {"readonly": True},
            "property_stock_customer": {"readonly": True},
            "property_stock_supplier": {"readonly": True},
            "title": {"readonly": True},
        },
        "res.partner.bank": {
            "bank_name": {"readonly": False},
        },
        "res.users": {
            "action_id": {"readonly": True},
            "category_id": {"readonly": True},
            "company_id": {"readonly": True},
            "login_date": {"readonly": True},
            "new_password": {"readonly": True},
            "opt_out": {"readonly": True},
            "password": {"readonly": True},
            "password_crypt": {"readonly": True},
        },
        "sale.order": {
            "name": {"readonly": False, "required": False},
        },
        "stock.picking.package.preparation": {
            "ddt_number": {"required": False},
        },
    }

    def get_distro_version(self, distro):
        """Return distro + version identifier used for translation
        Args:
            distro (str): odoo distribution, mey be ('odoo', 'zero', 'librerp')
        Returns:
            distro + version identifier (str)
        """
        if distro and not distro.startswith("odoo"):
            if distro == "powerp":
                distro_version = "librerp%d" % release.version_info[0]
            else:
                distro_version = "%s%d" % (distro, release.version_info[0])
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
            module = self.env["ir.module.module"].search([("name", "=", module)])
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
            raise UserError("Model %s not found!" % model_name)
        return self.env[model_name].fields_get()

    # def map_values(self, model_name, vals):
    #     if model_name not in self.env:
    #         raise UserError(
    #             'Model %s not found!' % model_name)
    #     struct = self.env[model_name].fields_get()
