# -*- coding: utf-8 -*-
"""Test Environment v2.0.2.1

Copy this file in tests directory of your module.
Please copy the documentation testenv.rst file too in your module.
The __init__.py must import testenv.
Your python test file should have to contain some following example lines:

    import os
    import logging
    from .testenv import MainTest as SingleTransactionCase

    _logger = logging.getLogger(__name__)

    TEST_RES_PARTNER = {...}
    TEST_SETUP_LIST = ["res.partner", ]

    class MyTest(SingleTransactionCase):

        def setUp(self):
            super().setUp()
            # Add following statement just for get debug information
            self.debug_level = 0
            data = {"TEST_SETUP_LIST": TEST_SETUP_LIST}
            for resource in TEST_SETUP_LIST:
                item = "TEST_%s" % resource.upper().replace(".", "_")
                data[item] = globals()[item]
            self.declare_all_data(data)     # TestEnv swallows the data
            self.setup_env()                # Create test environment

        def tearDown(self):
            super().tearDown()
            if os.environ.get("ODOO_COMMIT_TEST", ""):
                # Save test environment, so it is available to dump
                self.env.cr.commit()     # pylint: disable=invalid-commit
                _logger.info("✨ Test data committed")

        def test_mytest(self):
            _logger.info(
                "🎺 Testing test_mytest"    # Use unicode char to best log reading
            )
            ...

        def test_mywizard(self):
            self.wizard(...)                # Test requires wizard simulator

For furthermore information, please:
* Read file testenv.rst in this directory (if supplied)
* Visit https://zeroincombenze-tools.readthedocs.io
* Visit https://github.com/zeroincombenze/tools
"""
from __future__ import unicode_literals
from future.utils import PY2, PY3
from past.builtins import basestring, long

# import sys
import logging
from collections import defaultdict
import base64

from odoo.tools.safe_eval import safe_eval

import python_plus
from z0bug_odoo.test_common import SingleTransactionCase
from z0bug_odoo import z0bug_odoo_lib

_logger = logging.getLogger(__name__)

RESOURCE_WO_COMPANY = ("res.users",)
if PY3:
    text_type = unicode = str                                        # pragma: no cover
    bytestr_type = bytes                                             # pragma: no cover
elif PY2:
    # unicode exist only for python2
    text_type = unicode                                              # pragma: no cover
    bytestr_type = str                                               # pragma: no cover


class MainTest(SingleTransactionCase):
    def setUp(self):
        super(MainTest, self).setUp()
        self.debug_level = 0
        self.PYCODESET = 'utf-8'
        self._logger = _logger
        self.setup_data_list = {}
        self.setup_data = {}
        self.struct = {}
        self.skeys = {}
        self.parent_name = {}
        self.parent_resource = {}
        self.childs_name = {}
        self.childs_resource = {}
        self.uninstallable_modules = []
        self.tnxl_record = {}

    def u(self, s):
        if isinstance(s, bytestr_type):
            if PY3:
                return s.decode(self.PYCODESET)
            return unicode(s, self.PYCODESET)
        return s

    def unicodes(self, src):
        if isinstance(src, dict):
            src2 = src.copy()
            for x in src2.keys():
                if isinstance(x, bytestr_type):
                    del src[x]
                src[self.u(x)] = self.u(src2[x])
        elif isinstance(src, (list, tuple)):
            for i, x in enumerate(src):
                src[i] = self.u(x)
        return src

    def default_company(self):
        return self.env.user.company_id

    def _is_xref(self, xref):
        return (isinstance(xref, basestring)
                and "." in xref
                and " " not in xref
                and len(xref.split(".")) == 2)

    def add_translation(self, resource, field, tnxl):
        self._logger.info(
            "⚠ %s[%s]: '%s' -> '%s'" % (resource, field, tnxl[0], tnxl[1])
        )
        if resource not in self.tnxl_record:
            self.tnxl_record[resource] = {}
        self.tnxl_record[resource][field] = tnxl

    def add_translation_xref(self, xref, xref_tnxl):
        self._logger.info(
            "⚠ xref '%s' -> '%s'" % (xref, xref_tnxl)
        )
        resource = "ir.model.data"
        if resource not in self.tnxl_record:
            self.tnxl_record[resource] = {}
        self.tnxl_record[resource][xref] = xref_tnxl

    def tnxl_field_value(self, resource, field, value, fmt=None):
        if (
            fmt
            and resource in self.tnxl_record
            and field in self.tnxl_record[resource]
            and value == self.tnxl_record[resource][field][0]
        ):
            value = self.tnxl_record[resource][field][1]
        elif (
            self._is_xref(value)
            and "ir.model.data" in self.tnxl_record
            and value in self.tnxl_record["ir.model.data"]
        ):
            value = self.tnxl_record["ir.model.data"][value]
        return value

    def compute_date(self, date, refdate=None):
        """Compute data

        Args:
            date (date or string or integer): formula
            refdate (date or string): reference date

        Returns:
            ISO format string with result date

        """
        return python_plus.compute_date(date, refdate=refdate)

    def _search4parent(self, resource, parent_resource=None):
        if resource == "product.product":
            parent_resource = "product.template"
        else:
            parent_resource = parent_resource or ".".join(resource.split(".")[:-1])
        if parent_resource not in self.env:
            parent_resource = None
        if parent_resource and resource not in self.parent_resource:
            for field in self.struct[resource].keys():
                if self.struct[resource][field].get("relation", "/") == parent_resource:
                    self.parent_name[resource] = field
                    self.parent_resource[resource] = parent_resource
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞parent_resource[%s] = %s" % (
                                resource, self.parent_resource[resource])
                        )
                        self._logger.info(
                            "🐞parent_name[%s] = %s" % (resource, field)
                        )
                    break

    def _search4childs(self, resource, childs_resource=None):
        childs_resource = childs_resource or []
        if not childs_resource:
            if resource == "product.template":
                childs_resource = ["product.product"]
            else:
                for suffix in (".line", ".rate", ".state"):
                    childs_resource.append(resource + suffix)
        if not isinstance(childs_resource, (list, tuple)):
            childs_resource = [childs_resource]                      # pragma: no cover
        if resource not in self.childs_resource:
            for field in sorted(self.struct[resource].keys()):
                if (not field.startswith("valid_")
                        and self.struct[resource][field].get("relation",
                                                             "/") in childs_resource):
                    self.childs_name[resource] = field
                    self.childs_resource[resource] = self.struct[resource][field][
                        "relation"
                    ]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞childs_resource[%s] = %s" % (
                                resource, self.childs_resource[resource])
                        )
                        self._logger.info(
                            "🐞childs_name[%s] = %s" % (resource, field)
                        )
                    break

    def _load_field_struct(self, resource):
        """Load Odoo field definition"""
        if resource not in self.struct:
            if resource not in self.env:
                raise ValueError(                                    # pragma: no cover
                    "Model %s not found in the system" % resource)   # pragma: no cover
            self.struct[resource] = self.env[resource].fields_get()
            self._search4parent(resource)
            if resource in self.parent_resource:
                self._load_field_struct(self.parent_resource[resource])
                self._search4childs(self.parent_resource[resource])
            self._search4childs(resource)
            if resource in self.childs_resource:
                self._load_field_struct(self.childs_resource[resource])
                self._search4parent(self.childs_resource[resource])
            multi_key = True if self.parent_name.get(resource) else False
            # Please, do not change fields order
            fields = (
                "acc_number",
                "code_prefix",
                "default_code",
                "sequence",
                "login",
                "description",
                "depreciation_type_id",
                "number",
                "partner_id",
                "product_id",
                "product_tmpl_id",
                "tax_src_id",
                "tax_dest_id",
                "code",
                "name",
            )
            for field in fields:
                if (
                    field == self.parent_name.get(resource)
                    or (field == "code" and resource == "product.product")
                    or (field == "description" and resource != "account.tax")
                    or (field == "login" and resource != "res.users")
                    or (field == "sequence" and not multi_key)
                ):
                    continue                                         # pragma: no cover
                if field in self.struct[resource]:
                    self.skeys[resource] = [field]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞skeys[%s] = %s" % (resource, self.skeys[resource])
                        )
                    break

    def _add_xref(self, xref, xid, resource):
        """Add external reference ID that will be used in next tests.
        If xref exist, result ID will be upgraded"""
        module, name = xref.split(".", 1)
        if module == "external":
            return False
        ir_model = self.env["ir.model.data"]
        values = {
            "module": module,
            "name": name,
            "model": resource,
            "res_id": xid,
        }
        xrefs = ir_model.search([("module", "=", module), ("name", "=", name)])
        if not xrefs:
            return ir_model.create(values)
        xrefs[0].write(values)
        return xrefs[0]

    def _get_xref_id(self, resource, xref, fmt=None):
        res = xref
        if xref.isdigit() or xref.startswith("-") and xref[1:].isdigit():
            res = int(xref)
        elif self._is_xref(xref):
            if fmt:
                res = self.resource_bind(
                    xref, raise_if_not_found=False, resource=resource
                )
                if not res and not self.get_resource_data(resource, xref):
                    self._logger.info("⚠ External reference %s not found" % xref)
            else:
                res = self.env.ref(
                    self.tnxl_field_value(resource, None, xref),
                    raise_if_not_found=False)
            res = res.id if res else False if fmt else xref
        return res

    def _cast_2many(self, resource, value, fmt=None, group=None):
        """"One2many and many2many may have more representations:
        * External reference (str) -> 1 value or None
        * list() or list (str)
        * - [0, 0, values (dict)]
        * - [1, ID (int), values (dict)]
        * - [2, ID (int), x]
        * - [3, ID (int), x]
        * - [4, ID (int), x]
        * - [5, x, x]
        * - [6, x, IDs (list)]
        * - External reference (str) -> 1 value or None
        """

        def value2list(value):
            if isinstance(value, basestring):
                value = [x for x in value.split(",")]
            elif not isinstance(value, (list, tuple)):
                value = [value]
            return value

        res = []
        is_cmd = True if isinstance(value, (list, tuple)) else False
        # childs_resource = self.childs_resource.get(resource)
        items = value2list(value)
        for item in items:
            if isinstance(item, basestring):
                xid = self._get_xref_id(resource, item, fmt=fmt)
                if xid:
                    res.append(xid)
                is_cmd = False
            elif (
                fmt
                and is_cmd
                and isinstance(item, (list, tuple))
                and len(item) == 3
                and item[0] in (0, 1)
                and isinstance(item[2], basestring)
            ):
                res.append(
                    (
                        item[0],
                        item[1],
                        self.cast_types(
                            resource,
                            self.get_resource_data(
                                resource, item[2], group=group),
                            fmt=fmt,
                            group=group
                        ),
                    )
                )
            elif (
                fmt
                and is_cmd
                and isinstance(item, (list, tuple))
                and len(item) in (2, 3)
                and (
                    (len(item) == 3 and item[0] == 0 and isinstance(item[2], dict))
                    or (
                        len(item) == 3
                        and item[0] == 1
                        and isinstance(item[1], (int, long))
                        and isinstance(item[2], dict)
                    )
                    or (
                        len(item) == 2
                        and item[0] in (2, 3, 4)
                        and isinstance(item[1], (int, long))
                    )
                    or item[0] == 5
                    or (
                        len(item) == 3
                        and item[0] == 6
                        and isinstance(item[1], (int, long))
                        and isinstance(item[2], (list, tuple))
                    )
                )
            ):
                res.append(item)
            elif isinstance(item, (list, tuple)):
                res.append(self._cast_2many(resource, item, group=group))
                is_cmd = False
            else:
                res.append(item)
                is_cmd = False
        if len(res):
            if fmt == "cmd" and not is_cmd:
                res = [(6, 0, res)]
        else:
            res = False
            if fmt:
                self._logger.info("⚠ No *2many value for %s.%s" % (resource, value))
        return res

    def _check_4_selection(self, resource, field, value, fmt=None):
        if fmt and resource == "res.partner" and field == "lang":
            if not self.env["res.lang"].search([("code", "=", value)]):
                self._logger.info("⚠ Invalid value %s" % value)
                value = None
        return value

    def _add_child_records(self, resource, xref, values, group=None):
        if resource not in self.childs_name:
            return values
        field = self.childs_name[resource]
        if values.get(field):
            return values
        values[field] = []
        childs_resource = self.childs_resource[resource]
        for child_xref in self.get_resource_data_list(childs_resource, group=group):
            if child_xref.startswith(xref):
                obj = self.resource_bind(
                    child_xref, raise_if_not_found=False, resource=childs_resource,
                )
                if obj:
                    values[field].append((1, obj.id, child_xref))
                else:
                    values[field].append((0, 0, child_xref))
        return values

    def _get_depending_xref(self, resource, xref):
        resource_child = xref_child = field_child = field_parent = False
        if resource == "product.template":
            xref_child = xref.replace("_template", "_product")
            if xref_child == xref:
                xref_child = xref.replace("template_", "product_")
            if xref_child == xref:
                xref_child = xref.replace("template", "product")
            if xref_child == xref:                                   # pragma: no cover
                self._logger.info(                                   # pragma: no cover
                    (                                                # pragma: no cover
                        "⚠ wrong xref pattern '%s':"                 # pragma: no cover
                        " please use something like 'z0bug.product_template_1"
                    ) % xref                                         # pragma: no cover
                )                                                    # pragma: no cover
                xref_child = False                                   # pragma: no cover
            else:
                self._logger.info(
                    "xref ('product.template') '%s' -> ('product.product') '%s'"
                    % (xref, xref_child)
                )
                resource_child = self.childs_resource[resource]
                field_child = self.childs_name[resource]
                field_parent = "product_tmpl_id"
        return resource_child, xref_child, field_child, field_parent

    def _adjust_test_data(self, group=None):
        for (debug_xref, tnxl_xref) in (
            ("z0bug.partner_mycompany", "base.main_company"),
        ):
            res = self.env.ref(debug_xref, raise_if_not_found=False)
            if not res:
                self.add_translation_xref(debug_xref, tnxl_xref)
        if not self.env["ir.module.module"].search(
            [("name", "=", "stock"), ("state", "=", "installed")]
        ):
            for resource in ("product.product", "product.template"):
                self.add_translation(resource, "type", ["product", "consu"])
        if not self.env["ir.module.module"].search(
            [("name", "=", "account_payment_term_extension"),
             ("state", "=", "installed")]
        ):
            resource = "account.payment.term.line"
            for xref in self.get_resource_data_list(resource, group=group):
                values = self.get_resource_data(resource, xref, group=group)
                if values.get("months"):
                    values["days"] = values["months"] * 30 - 2
                    values["months"] = ""
                self.store_resource_data(resource, xref, values, group=group)

    def cast_types(self, resource, values, fmt=None, group=None):
        self._load_field_struct(resource)
        for field in [x for x in values.keys()]:
            values[field] = self.tnxl_field_value(
                resource, field, values[field], fmt=fmt)
            value = values[field]
            if value is None or value in ("None", r"\N") or field == "id":
                del values[field]
                if self.debug_level > 1:
                    self._logger.info(
                        "🐞del %s.vals[%s]" % (resource, field)
                    )
                continue
            if field not in self.struct[resource]:
                if fmt:
                    del values[field]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞field %s does not exist in %s" % (field, resource)
                        )
                continue
            ftype = self.struct[resource][field]["type"]
            if field == "company_id":
                if fmt and not value and resource not in RESOURCE_WO_COMPANY:
                    values[field] = self.default_company().id
                continue
            elif ftype == "boolean":
                if isinstance(value, basestring):
                    if value.isdigit():
                        values[field] = eval(value)
                    elif (
                        not value
                        or value.lower().startswith("f")
                        or value.lower().startswith("n")
                    ):
                        values[field] = False
                    else:
                        values[field] = True
            elif ftype in ("float", "monetary") and isinstance(value, basestring):
                values[field] = eval(value)
            elif ftype in ("date", "datetime") and isinstance(value, basestring):
                values[field] = self.compute_date(value)
            elif ftype in ("date", "datetime") and isinstance(value, (list, tuple)):
                if fmt:
                    values[field] = self.compute_date(value[0], refdate=value[1])
            elif ftype in ("many2one", "integer") and isinstance(value, basestring):
                values[field] = self._get_xref_id(
                    self.struct[resource][field].get("relation", resource),
                    value,
                    fmt=fmt,
                )
                if not values[field]:
                    del values[field]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞no value for %s.%s" % (resource, field)
                        )
                    continue
            elif ftype in ("one2many", "many2many"):
                values[field] = self._cast_2many(
                    self.struct[resource][field]["relation"],
                    value,
                    fmt=fmt,
                    group=group
                )
                if not values[field]:
                    del values[field]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞no value for %s.%s" % (resource, field)
                        )
                    continue
            elif ftype == "selection":
                values[field] = self._check_4_selection(resource, field, value, fmt=fmt)
                if not values[field]:
                    del values[field]
                    if self.debug_level > 1:
                        self._logger.info(
                            "🐞no value for %s.%s" % (resource, field)
                        )
                    continue
            values[field] = self.tnxl_field_value(
                resource, field, values[field], fmt=fmt)
        if self.debug_level > 1 and not values:
            self._logger.info(
                "🐞cast_type(%s, %s) -> null" % (resource, values)
            )
        return values

    def store_resource_data(self, resource, xref, values, group=None, name=None):
        group = self.u(group) or "base"
        name = self.u(name) or self.u(resource)
        if group not in self.setup_data_list:
            self.setup_data_list[group] = []
            self.setup_data[group] = {}
        if name not in self.setup_data[group]:
            self.setup_data[group][name] = {}
        self.setup_data[group][name][xref] = self.cast_types(
            resource, values, group=group)
        if self.debug_level > 1:
            self._logger.info(
                "🐞%s.store_resource_data(%s,%s,group=%s)" % (
                    resource, xref, name, group)
            )
        if name not in self.setup_data_list[group]:
            self.setup_data_list[group].append(name)

    def resource_bind(self, xref, raise_if_not_found=True, resource=None):
        """Simulate External Reference
        This function simulates self.env.ref() searching for resource record.
        Ordinary xref is formatted as "MODULE.NAME"; when MODULE == "external"
        this function is engaged.

        Args:
            xref (str): external reference
            raise_if_not_found (bool): raise exception if xref not found or
                                       if more records found
            resource (str): Odoo model name

        Returns:
            obj: the Odoo model record
        """
        if self.debug_level > 2:
            self._logger.info(
                "🐞%s.resource_bind(%s)" % (resource, xref)
            )
        # Search for Odoo standard external reference
        obj = self.env.ref(
            self.tnxl_field_value(resource, None, xref), raise_if_not_found=False)
        if obj:
            return obj
        # Simulate external reference
        if not resource:
            if raise_if_not_found:                                   # pragma: no cover
                raise TypeError(                                     # pragma: no cover
                    "No model issued for binding"                    # pragma: no cover
                )                                                    # pragma: no cover
            return False                                             # pragma: no cover
        if resource not in self.env:
            if raise_if_not_found:                                   # pragma: no cover
                raise ValueError(                                    # pragma: no cover
                    "Model %s not found in the system" % resource    # pragma: no cover
                )                                                    # pragma: no cover
            return False                                             # pragma: no cover
        self._load_field_struct(resource)
        if resource not in self.skeys:
            if raise_if_not_found:
                raise TypeError(                                     # pragma: no cover
                    "Model %s without search key" % resource         # pragma: no cover
                )                                                    # pragma: no cover
            self._logger.info("⚠ Model %s without search key" % resource)
            return False
        module, name = xref.split(".", 1)
        parent_name = self.parent_name.get(resource)
        if parent_name and self.parent_resource[resource] in self.childs_resource:
            # This is a 3 level external reference for header/detail relationship
            x = name.split("_")
            # Actual external reference for parent record
            name = "_".join(x[:-1])
            # Key to search for child record
            x = x[-1]
            if x.isdigit():
                while x.startswith("0"):
                    x = x[1:]
                if not x:
                    return False
                x = eval(x)
            if self.struct[resource][self.skeys[resource][0]]["type"] == "many2one":
                pass
            domain = [(self.skeys[resource][0], "=", x)]
            x = self.resource_bind(
                "%s.%s" % (module, name),
                resource=self.parent_resource[resource],
                raise_if_not_found=False,
            )
            if not x:
                return False
            domain.append((parent_name, "=", x.id))
        else:
            domain = [(self.skeys[resource][0], "=", name)]
        if (
            resource not in RESOURCE_WO_COMPANY
            and "company_id" in self.struct[resource]
        ):
            domain.append("|")
            domain.append(("company_id", "=", self.default_company().id))
            domain.append(("company_id", "=", False))
        obj = self.env[resource].search(domain)
        if len(obj) == 1:
            return obj[0]
        if raise_if_not_found:
            raise ValueError("External ID %s not found" % xref)      # pragma: no cover
        return False

    def resource_create(self, resource, values=None, xref=None, group=None):
        """Create a test record and set external ID to next tests"""
        self._load_field_struct(resource)
        if not values and xref:
            values = self.get_resource_data(resource, xref, group=group)
            values = self._add_child_records(resource, xref, values, group=group)
        if not values:
            raise ValueError(                                        # pragma: no cover
                "No value supplied for %s create" % resource         # pragma: no cover
            )                                                        # pragma: no cover
        if self.debug_level > 2:
            self._logger.info(
                "🐞%s.resource_create(%s,%s)" % (resource, values, xref)
            )
        values = self.cast_types(resource, values, fmt="cmd", group=group)
        if resource.startswith("account.move"):
            res = (
                self.env[resource]
                .with_context(check_move_validity=False)
                .create(values)
            )
        else:
            res = self.env[resource].create(values)
        if self._is_xref(xref):
            self._add_xref(xref, res.id, resource)
            self.store_resource_data(resource, xref, values, group=group)
            (
                resource_child, xref_child, field_child, field_parent
            ) = self._get_depending_xref(resource, xref)
            if resource_child and xref_child:
                self._add_xref(
                    xref_child, getattr(res, field_child)[0].id, resource_child)
                values_child = {k: v for (k, v) in values.items()}
                values_child[field_parent] = res.id
                self.store_resource_data(
                    resource_child, xref_child, values_child, group=group)
        return res

    def resource_write(
        self, resource, xref, values=None, raise_if_not_found=True, group=None
    ):
        """Update a test record with external"""
        obj = self.resource_bind(
            xref, resource=resource, raise_if_not_found=raise_if_not_found
        )
        if obj:
            if not values:
                values = self.get_resource_data(resource, xref, group=group)
            values = self._add_child_records(resource, xref, values, group=group)
            values = self.cast_types(resource, values, fmt="cmd", group=group)
            if self.debug_level > 2:
                self._logger.info(
                    "🐞%s.resource_write(%s,%s)" % (resource, values, xref)
                )
            if resource.startswith("account.move"):
                obj.with_context(check_move_validity=False).write(values)
            else:
                obj.write(values)
        return obj

    def resource_make(self, resource, xref, values=None, group=None):
        """Create or write a test record and set external ID to next tests"""
        if self.debug_level > 2:
            self._logger.info(
                "🐞%s.resource_make(%s,%s)" % (resource, values, xref)
            )
        obj = self.resource_write(
            resource, xref, values=values, raise_if_not_found=False, group=group
        )
        if not obj:
            obj = self.resource_create(resource, values=values, xref=xref, group=group)
        return obj

    def declare_resource_data(self, resource, data, name=None, group=None, merge=None):
        """Declare data to load on setup_env().

        Args:
            resource (str): Odoo model name, i.e. "res.partner"
            data (dict): record data
            name (str): label of dataset; default is resource name
            group (str): used to manager group data; default is "base"
            merge (str): merge data with public data (currently just "zerobug")
        Raises:
            TypeError: if invalid parameters issued
        """
        if not isinstance(data, dict):
            raise TypeError("Dictionary expected")                   # pragma: no cover
        if merge and merge != "zerobug":
            raise ValueError("Invalid merge value: use 'zerobug'")   # pragma: no cover
        data = self.unicodes(data)
        for xref in sorted(data.keys()):
            if merge == "zerobug":
                zerobug = z0bug_odoo_lib.Z0bugOdoo().get_test_values(resource, xref)
                for field in zerobug.keys():
                    if field not in data[xref]:
                        data[xref][field] = zerobug[field]
            data[xref] = self.unicodes(data[xref])
            self.store_resource_data(resource, xref, data[xref], group=group, name=name)

    def declare_all_data(self, message, group=None, merge=None):
        """Declare all data to load on setup_env().

        Args:
            message (dict): data message
                TEST_SETUP_LIST (list): resource list to load
                TEST_* (dict): resource data; * is the uppercase resource name where
                               dot are replaced by "_"; (see declare_resource_data)
            group (str): used to manager group data; default is "base"
            merge (str): merge data with public data (currently just "zerobug")
        Raises:
            TypeError: if invalid parameters issued
        """
        if not isinstance(message, dict):
            raise TypeError("Dictionary expected")                   # pragma: no cover
        if "TEST_SETUP_LIST" not in message:
            raise TypeError("Key TEST_SETUP_LIST not found")         # pragma: no cover
        group = group or "base"
        for resource in message["TEST_SETUP_LIST"]:
            item = "TEST_%s" % resource.upper().replace(".", "_")
            if item not in message:
                raise TypeError("Key %s not found" % item)           # pragma: no cover
        for resource in message["TEST_SETUP_LIST"]:
            if self.debug_level:
                self._logger.info(
                    "🐞declare_all_data(%s, %s)" % (resource, group)
                )
            item = "TEST_%s" % resource.upper().replace(".", "_")
            self.declare_resource_data(
                resource, message[item], group=group, merge=merge
            )

    def get_resource_data(self, resource, xref, group=None):
        """Get declared resource data; may be used to test compare.

        Args:
            resource (str): Odoo model name or name assigned, i.e. "res.partner"
            xref (str): external reference
            group (str): if supplied select specific group data; default is "base"

        Returns:
            dictionary with data
        """
        group = group or "base"
        if (
            group in self.setup_data
            and resource in self.setup_data[group]
            and xref in self.setup_data[group][resource]
        ):
            return self.setup_data[group][resource][xref]
        return {}                                                    # pragma: no cover

    def get_resource_data_list(self, resource, group=None):
        """Get declared resource data list.

        Args:
            resource (str): Odoo model name or name assigned, i.e. "res.partner"
            group (str): if supplied select specific group data; default is "base"

        Returns:
            list of data
        """
        group = group or "base"
        if group in self.setup_data and resource in self.setup_data[group]:
            return list(self.setup_data[group][resource].keys())
        return []                                                    # pragma: no cover

    def get_resource_list(self, group=None):
        """Get declared resource list.

        Args:
            group (str): if supplied select specific group data; default is "base"
        """
        group = group or "base"
        if group in self.setup_data_list:
            return self.setup_data_list[group]
        return []                                                    # pragma: no cover

    def set_locale(self, locale_name, raise_if_not_found=True):
        modules_model = self.env["ir.module.module"]
        modules = modules_model.search([("name", "=", locale_name)])
        if modules and modules[0].state != "uninstalled":
            modules = []
        if modules:
            modules.button_immediate_install()
            self.env["account.chart.template"].try_loading_for_current_company(
                locale_name
            )
        else:
            if raise_if_not_found:
                raise ValueError("Module %s not found in the system" % locale_name)

    def install_language(self, iso, overwrite=None, force_translation=None):
        iso = iso or "en_US"
        overwrite = overwrite or False
        load = False
        lang_model = self.env["res.lang"]
        languages = lang_model.search([("code", "=", iso)])
        if not languages:
            languages = lang_model.search([("code", "=", iso), ("active", "=", False)])
            if languages:
                languages.write({"active": True})
                load = True
        if not languages or load:
            vals = {
                "lang": iso,
                "overwrite": overwrite,
            }
            self.env["base.language.install"].create(vals).lang_install()
        if force_translation:
            vals = {"lang": iso}
            self.env["base.update.translations"].create(vals).act_update()

    def setup_env(
        self,
        lang=None,
        locale=None,
        group=None,
        enable_cancel_journal=None
    ):
        """Create all record from declared data. See above doc

        Args:
            lang (str): install & load specific language
            locale (str): install locale module with CoA; i.e l10n_it

        Returns:
            None
        """
        self._logger.info("🎺 Starting test")
        if locale:
            self.set_locale(locale)
        if lang:
            self.install_language(lang)
        self._adjust_test_data(group=group)
        for resource in self.get_resource_list(group=group):
            for xref in self.get_resource_data_list(resource, group=group):
                self.resource_make(resource, xref)
        if enable_cancel_journal:
            self.env["account.journal"].search([]).write({"update_posted": True})

    def resource_edit(
        self, resource, default=None, web_changes=None, actions=None, save=None
    ):
        """Simulate web editing
        Args:
            resource (str or obj): if field is a string simulate create web behavior of
                                   Odoo model issued in resource;
                                   if field is an obj simulate write web behavior on the
                                   issued record
            default (dict): default value to assign
            web_changes (list): list of tuples (field, value); see <wizard_edit>
        """
        default = default or {}
        actions = actions or []
        actions = actions if isinstance(actions, (list, tuple)) else [actions]
        if isinstance(resource, basestring):
            # TODO> record = self.env[resource].new(values=default)
            resource_model = resource
            record = object.__new__(self.env[resource].__class__)
            record.env = self.env
            record._ids = [0]
            record._prefetch = defaultdict(set)
            for field in self.env[resource]._fields.keys():
                if field == "id":
                    continue
                setattr(record, field, default.get(field, False))
            for field in record._fields.values():
                if field.default:
                    field.default(record)
            # Get all onchange method names and run them with None values
            # record = record if isinstance(record, (list, tuple)) else [record]
            for field in record._onchange_methods.values():
                for method in field:
                    method(record)
        else:
            resource_model = resource._name
            record = resource
        web_changes = web_changes or []
        for args in web_changes:
            self.wizard_edit(
                record, args[0], args[1], args[2] if len(args) > 2 else None
            )
        for action in actions:
            if action and hasattr(record, action):
                if self.debug_level > 1:
                    self._logger.info(
                        "🐞%s.%s" % (resource_model, action)
                    )
                getattr(record, action)()
        if save:
            if record.id:
                record.write({})
            else:
                record.create({})

    def resource_download(
        self,
        module=None,
        action_name=None,
        act_windows=None,
        records=None,
        default=None,
        ctx=None,
        button_name=None,
        web_changes=None,
        button_ctx=None,
        field=None,
    ):
        act_windows = self.wizard(
            module=module,
            action_name=action_name,
            act_windows=act_windows,
            records=records,
            default=default,
            ctx=ctx,
            button_name=button_name,
            web_changes=web_changes,
            button_ctx=button_ctx,
        )
        if field not in self.env[act_windows["res_model"]]:
            raise ValueError(
                "Filed %s not found in %s" % (field, act_windows["res_model"]))
        return base64.decodestring(
            getattr(self.env[act_windows["res_model"]].browse(act_windows["res_id"]),
                    field))

    ########################################
    #     WIZARD ENVIRONMENT FUNCTIONS     #
    ########################################

    def is_action(self, act_windows):
        return isinstance(act_windows, dict) and act_windows.get("type") in (
            "ir.actions.act_window",
            "ir.actions.client",
        )

    def wizard_launch(
        self, act_windows, records=None, default=None, ctx=None, windows_break=None
    ):
        """Start a wizard from a windows action.

        This function simulates the wizard or action server starting web interface.
        It creates the wizard record with default values.
        It is useful to test:
            * view names
            * wizard structure
            * wizard code

        Args:
            act_windows (dict): Odoo windows action
            records (obj): objects required by action server
            default (dict): default value to assign
            ctx (dict): context to pass to wizard during execution
            windows_break (bool): if True breaks chain and avoid view test
                                  Warning: returns wizard image too

        Returns:
            Odoo windows action to pass to wizard execution
            If windows break return wizard image too
        """
        if self.debug_level > 1:
            self._logger.info(
                "🐞wizard starting(%s,ctx=%s)" % (act_windows, ctx)
            )
        if not isinstance(act_windows, dict):
            raise (TypeError, "Invalid act_windows")
        if isinstance(act_windows.get("context"), basestring):
            act_windows["context"] = safe_eval(
                act_windows["context"],
                self.env["ir.actions.actions"]._get_eval_context(),
            )
        if ctx:
            if isinstance(act_windows.get("context"), dict):
                act_windows["context"].update(ctx)
            else:
                act_windows["context"] = ctx
            if ctx.get("res_id"):
                act_windows["res_id"] = ctx.pop("res_id")
        if records:
            if records._name != act_windows.get(
                "model_name", act_windows.get(
                    "src_model", act_windows["res_model"])):
                raise (TypeError, "Records model different from declared model")
            if not iter(records):
                records = [records]
        if act_windows["type"] == "ir.actions.server":
            if not records:
                raise (TypeError, "No records supplied")
            wizard = records
        else:
            if records:
                act_windows["context"]["active_ids"] = [x.id for x in records]
                if len(records) == 1:
                    act_windows["context"]["active_id"] = records[0].id
                else:
                    act_windows["context"]["active_id"] = 0
            res_model = act_windows["res_model"]
            vals = self.cast_types(res_model, default or {})
            res_id = act_windows.get("res_id")
            if res_id:
                wizard = self.env[res_model].with_context(
                    act_windows["context"]).browse(res_id)
            else:
                wizard = self.env[res_model].with_context(
                    act_windows["context"]).create(vals)
                act_windows["res_id"] = wizard.id
        # Save wizard for furthermore use
        # act_windows["_wizard_"] = wizard
        if windows_break:
            return act_windows, wizard
        if act_windows.get("view_id"):
            # This code is just executed to test valid view structure
            self.env["ir.ui.view"].browse(act_windows["view_id"])
        return act_windows

    def wizard_launch_by_act_name(
        self,
        module,
        action_name,
        records=None,
        default=None,
        ctx=None,
        windows_break=None,
    ):
        """Start a wizard from an action name.

        Validate the action name for xml view file, then call <wizard_start>

        *** Example ***

        XML view file:
            <record id="action_example" model="ir.actions.act_window">
                <field name="name">Example</field>
                <field name="res_model">wizard.example</field>
                [...]
            </record>

        Python code:
            act_windows = self.wizard_start_by_act_name(
                "module_example",   # Module name
                "action_example",   # Action name from xml file
            )

        Args:
            module (str): module name with wizard to test
            action_name (str): action name
            default (dict), ctx (dict), windows_break (bool): see above <wizard_start>
            records (obj): objects supplied for action server

        Returns:
            Same of <wizard_start>
        """
        act_model = "ir.actions.act_window"
        if module == ".":
            for item in self.__module__.split("."):
                if item not in ("odoo", "openerp", "addons"):
                    module = item
                    break
        act_windows = self.env[act_model].for_xml_id(module, action_name)
        return self.wizard_launch(
            act_windows,
            default=default,
            ctx=ctx,
            windows_break=windows_break,
            records=records,
        )

    def wizard_edit(self, wizard, field, value, onchange=None):
        """Simulate view editing on a field.

        Assign value to field, then engage all onchange functions on current field and
        on all updated fields.
        Finally, run onchange function issued by caller.
        Internal function of <wizard_execution>

        Args:
            wizard (object): execution wizard image
            field (str): field name which value is to assign
            value (any): value to assign to field; if None no assignment is made
            onchange (str): onchange function to execute after assignment

        Returns:
            None
        """
        if self.debug_level > 2:
            self._logger.info(
                "🐞wizard.onchange(%s,%s=%s)" % (wizard, field, value)
            )
        cur_vals = {}
        for name in wizard._fields.keys():
            cur_vals[name] = getattr(wizard, name)
        if value is not None:
            setattr(wizard, field, value)
        user_act = True
        while user_act:
            user_act = False
            for field in wizard._fields.keys():
                if (
                    cur_vals[field] != getattr(wizard, field)
                    and field in wizard._onchange_methods
                ):
                    user_act = True
                    for method in wizard._onchange_methods[field]:
                        method(wizard)
                cur_vals[field] = getattr(wizard, field)
        if onchange:
            getattr(wizard, onchange)()

    def wizard_execution(
        self,
        act_windows,
        records=None,
        button_name=None,
        web_changes=None,
        button_ctx=None,
        windows_break=None,
    ):
        """Simulate wizard execution issued by an action.

        Wizard is created by <wizard_start> with default values.
        First, execute onchange methods without values.
        Simulate user actions by web_changes that is a list of tuple (field, value);
            * fields are updated sequentially from web_changes parameters
            * a field can be updated more times
            * any updated engages the onchange funcion if defined for field
        Finally, the <button_name> function is executed.
        It returns the wizard result or False.

        Python example:
            act_window = self.wizard_execution(
                act_window,
                button_name="do_something",
                web_changes=[
                    ("field_a_ids", [(6, 0, [value_a.id])], "onchange_field_a"),
                    ("field_b_id", self.b.id, "onchange_field_b"),
                    ("field_c", "C"),
                ],
            )

        Args:
            act_windows (dict): Odoo windows action returned by <wizard_start>
            records (obj): objects supplied for action server
            button_name (str): function name to execute at the end of then wizard
            web_changes (list): list of tuples (field, value); see above <wizard_edit>
            button_ctx (dict): context to pass to button_name function
            windows_break (bool): if True breaks chain and avoid view test
                                  Warning: returns wizard image too

        Returns:
            Odoo wizard result; may be a windows action to engage another wizard
            If windows break return wizard image too

        Raises:
          TypeError: if invalid wizard image
        """

        if self.debug_level > 1:
            self._logger.info(
                "🐞wizard running(%s)" % (act_windows)
            )
        if act_windows["type"] == "ir.actions.server":
            if not records and "_wizard_" in act_windows:
                records = act_windows.pop("_wizard_")
            if not records:
                raise (TypeError, "No records supplied")
            if records._name != act_windows["model_name"]:
                raise (TypeError, "Records model different from declared model")
            ctx = {
                "active_model": act_windows["model_name"],
                "active_ids": [x.id for x in records],
            }
            eval_context = {
                "env": self.env,
                "model": records.with_context(ctx),
                "Warning": Warning,
                "record": records[0] if len(records) == 1 else None,
                "records": records,
                "log": self._logger,
            }
            eval_context.update(ctx)
            act_windows = safe_eval(
                act_windows["code"].strip(), eval_context, mode="exec", nocopy=True
            )
            return act_windows

        res_model = act_windows["res_model"]
        ctx = (
            safe_eval(act_windows.get("context"))
            if isinstance(act_windows.get("context"), basestring)
            else act_windows.get("context", {})
        )
        # if "_wizard_" in act_windows:
        #     wizard = act_windows.pop("_wizard_")
        if isinstance(act_windows.get("res_id"), (int, long)):
            wizard = self.env[res_model].with_context(ctx).browse(act_windows["res_id"])
        else:
            raise (TypeError, "Invalid object/model")
        # Get all onchange method names and run them with None values
        for field in wizard._onchange_methods.values():
            for method in field:
                method(wizard)
        # Set default values
        for default_value in [x for x in ctx.keys() if x.startswith("default_")]:
            field = default_value[8:]
            setattr(wizard, field, ctx[default_value])
            self.wizard_edit(wizard, field, ctx[default_value])
        # Now simulate user update action
        web_changes = web_changes or []
        for args in web_changes:
            self.wizard_edit(
                wizard, args[0], args[1], args[2] if len(args) > 2 else None
            )
        # Now simulate user confirmation
        # button_name = button_name or "process"
        if button_name and hasattr(wizard, button_name):
            if self.debug_level > 1:
                self._logger.info(
                    "🐞%s.%s" % (res_model, button_name)
                )
            result = getattr(wizard, button_name)()
            if isinstance(result, dict) and result.get("type") != "":
                result.setdefault("type", "ir.actions.act_window_close")
                if isinstance(button_ctx, dict):
                    result.setdefault("context", button_ctx)
                if (
                    self.is_action(result)
                    and result["type"] == "ir.actions.client"
                    and result.get("context", {}).get("active_model")
                    and result.get("context", {}).get("active_id")
                ):
                    result = self.env[result["context"]["active_model"]].browse(
                        result["context"]["active_id"]
                    )
            if windows_break:
                return result, wizard
            return result
        if windows_break:
            return False, wizard
        return False

    def wizard(
        self,
        module=None,
        action_name=None,
        act_windows=None,
        records=None,
        default=None,
        ctx=None,
        button_name=None,
        web_changes=None,
        button_ctx=None,
    ):
        """Execute full wizard in 1 step.

        Call <wizard_start> or <wizard__start_by_action_name>, then <wizard_execution>.
        All parameters are passed to specific functions.
        Both parameters <module> and <action_name> must be issued in order to
        call <wizard_by_action_name>.

        Args:
            see above <wizard_start>, <wizard__start_by_action_name> and
            <wizard_execution>

        Returns:
            Odoo wizard result; may be a windows action to engage another wizard
            If windows break return wizard image too

        Raises:
          TypeError: if invalid parameters issued
        """
        if module and action_name:
            act_windows = self.wizard_launch_by_act_name(
                module, action_name, records=records, default=default, ctx=ctx
            )
        elif act_windows:
            act_windows = self.wizard_launch(
                act_windows, records=records, default=default, ctx=ctx
            )
        else:
            raise (TypeError, "Invalid action!")
        return self.wizard_execution(
            act_windows,
            button_name=button_name,
            web_changes=web_changes,
            button_ctx=button_ctx,
        )
