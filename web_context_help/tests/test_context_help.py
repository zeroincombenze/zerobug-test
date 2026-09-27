# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
import json
import os
import shutil
import tempfile

from odoo.modules.module import get_module_path
from odoo.tests import common, tagged

BASE = """.. help-page:: partner
   :model: res.partner
   :view: base.view_partner_form

Partner
=======

.. _usage:

Usage
-----

Write the invoice address.
"""

INHERIT = """.. help-inherit:: wch_test_a.partner
   :section: usage
   :position: after

   Extra
   -----

   Additional carrier notes.
"""


@tagged("post_install", "-at_install")
class TestContextHelp(common.TransactionCase):
    def setUp(self):
        super(TestContextHelp, self).setUp()
        self.Page = self.env["context.help.page"]
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)
        self.dir_a = self._help_dir("a", {"common/partner.rst": BASE})
        self.dir_b = self._help_dir("b", {"common/extra.rst": INHERIT})
        own = os.path.join(get_module_path("web_context_help"), "help")
        self.modules = [
            ("web_context_help", own),
            ("wch_test_a", self.dir_a),
            ("wch_test_b", self.dir_b),
        ]

    def _help_dir(self, name, files):
        path = os.path.join(self.tmp, name, "help")
        for fn, text in files.items():
            full = os.path.join(path, fn)
            if not os.path.isdir(os.path.dirname(full)):
                os.makedirs(os.path.dirname(full))
            with open(full, "w") as fd:
                fd.write(text)
        return path

    def _rebuild(self):
        self.Page._wch_rebuild(self.modules, self.Page._wch_group())

    def test_own_pages_built(self):
        self.Page.sync_sources(force=True)
        pages = self.Page.search([("key", "=", "web_context_help.context_help_page")])
        self.assertEqual(sorted(pages.mapped("lang")), ["en_US", "it_IT"])
        en = pages.filtered(lambda p: p.lang == "en_US")
        self.assertIn("Editing a page", en.html)
        self.assertIn("Help pages", en.name)
        it = pages.filtered(lambda p: p.lang == "it_IT")
        self.assertIn("Modificare una pagina", it.html)
        self.assertTrue(en.section_ids.filtered(lambda s: s.question))
        self.assertFalse(self.Page.sync_sources())

    def test_rebuild_with_inherit(self):
        self._rebuild()
        page = self.Page.search([("key", "=", "wch_test_a.partner")])
        self.assertEqual(len(page), 1)
        self.assertEqual(page.model, "res.partner")
        html = page.html
        self.assertLess(html.index("invoice address"), html.index("carrier notes"))
        self.assertIn("extra", page.section_ids.mapped("label"))

    def test_edit_and_source_change(self):
        self._rebuild()
        page = self.Page.search([("key", "=", "wch_test_a.partner")])
        page.html = "<p>Company text</p>"
        self.assertTrue(page.edited)
        self._rebuild()
        self.assertFalse(page.source_changed)
        self.assertEqual(page.html, "<p>Company text</p>")
        with open(os.path.join(self.dir_a, "common/partner.rst"), "a") as fd:
            fd.write("\nNew paragraph.\n")
        self._rebuild()
        self.assertTrue(page.source_changed)
        self.assertEqual(page.html, "<p>Company text</p>")
        self.assertIn("New paragraph", page.source_html)
        page.action_reset_to_source()
        self.assertFalse(page.edited)
        self.assertFalse(page.source_changed)
        self.assertIn("New paragraph", page.html)

    def test_removed_source(self):
        self._rebuild()
        page = self.Page.search([("key", "=", "wch_test_a.partner")])
        page.html = "<p>Company text</p>"
        self.modules = self.modules[:1]
        self._rebuild()
        self.assertFalse(page.active)
        self.assertTrue(page.exists())

    def test_lookup(self):
        self._rebuild()
        form = self.env.ref("base.view_partner_form")
        page = self.Page.lookup(model="res.partner", view_type="form", view_id=form.id)
        self.assertEqual(page.key, "wch_test_a.partner")
        page = self.Page.lookup(model="res.partner", view_type="kanban")
        self.assertEqual(page.key, "wch_test_a.partner")
        self.assertFalse(self.Page.lookup(model="res.country", view_type="form"))
        self.Page.search([("key", "=", "wch_test_a.partner")]).view_type = "tree"
        page = self.Page.lookup(model="res.partner", view_type="list")
        self.assertEqual(page.key, "wch_test_a.partner")
        page = self.Page.lookup(
            model="context.help.page", view_type="form", lang="it_IT"
        )
        self.assertEqual(page.lang, "it_IT")
        page = self.Page.lookup(
            model="context.help.page", view_type="form", lang="fr_FR"
        )
        self.assertEqual(page.lang, "en_US")

    def test_fields_help(self):
        items = self.Page.fields_help("context.help.page")
        self.assertIn("key", [name for name, dummy, dummy2 in items])
        self.assertEqual(self.Page.fields_help("no.such.model"), [])

    def test_ask(self):
        self._rebuild()
        res = self.Page.ask("carrier notes", {"model": "res.partner"})
        self.assertEqual(res["provider"], "_wch_ask_fulltext")
        self.assertEqual(res["results"][0]["page_key"], "wch_test_a.partner")
        self.assertIn("#extra", res["results"][0]["url"])
        res = self.Page.ask("zzzqqq", {})
        self.assertFalse(res["results"])
        self.assertFalse(self.Page.ask("  ")["results"])
        log = self.env["context.help.question"].search([], limit=2)
        self.assertEqual(log.mapped("found"), [False, True])


@tagged("post_install", "-at_install")
class TestContextHelpHttp(common.HttpCase):
    def _json(self, url, params):
        # url_open() of this Odoo version sets no header: post through the opener
        res = self.opener.post(
            "http://%s:%s%s" % (common.HOST, common.PORT, url),
            data=json.dumps({"jsonrpc": "2.0", "method": "call", "params": params}),
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return res.json()["result"]

    def test_routes(self):
        self.env["context.help.page"].sync_sources(force=True)
        self.authenticate("admin", "admin")
        view = self.env.ref("web_context_help.context_help_page_form")
        res = self._json(
            "/web_context_help/lookup",
            {"model": "context.help.page", "view_type": "form", "view_id": view.id},
        )
        self.assertIn(
            "/web_context_help/page/web_context_help.context_help_page", res["url"]
        )
        res = self.url_open(res["url"])
        self.assertEqual(res.status_code, 200)
        self.assertIn("help_window.js", res.text)
        res = self._json("/web_context_help/lookup", {"model": "res.country"})
        self.assertIn("/web_context_help/auto/res.country", res["url"])
        self.assertEqual(self.url_open(res["url"]).status_code, 200)
        self.assertEqual(
            self.url_open("/web_context_help/page/no.page").status_code, 404
        )
        self.assertEqual(
            self.url_open("/web_context_help/auto/no.model").status_code, 404
        )
        res = self._json("/web_context_help/ask", {"question": "rebuilt checksum"})
        self.assertTrue(res["results"])
