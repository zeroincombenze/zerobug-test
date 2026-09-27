# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
import os
import shutil
import tempfile

from odoo.tests import common, tagged

from ..lib import html_page, rst_help

PAGE = """.. help-page:: partner
   :model: res.partner
   :view: base.view_partner_form, base.view_partner_tree
   :view-type: form

Partner
=======

.. help-include:: intro.rst

.. _usage:

Usage
-----

Fill :field:`Name <name>` as ``<first>.<last>`` then run :tour:`my_tour`.

.. help-question:: How to add a tag?

   Use the *Tags* field.

.. help-question::
   :auto:

Other
-----

Bye.
"""


@tagged("post_install", "-at_install")
class TestRstHelp(common.BaseCase):
    def setUp(self):
        super(TestRstHelp, self).setUp()
        self.help_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.help_dir)
        for subdir in ("common", "v16_20", "v10"):
            os.mkdir(os.path.join(self.help_dir, subdir))
        self._write("common/intro.rst", "Common **intro**.\n")
        self._write("common/intro.it_IT.rst", "Introduzione comune.\n")
        self._write("v10/intro.rst", "Intro for 10.\n")
        self._write("common/page.rst", PAGE)

    def _write(self, name, text):
        with open(os.path.join(self.help_dir, name), "w") as fd:
            fd.write(text)

    def _parse(self, group="v16_20", lang="en_US"):
        return rst_help.parse_file(
            os.path.join(self.help_dir, "common/page.rst"),
            self.help_dir,
            group,
            lang,
            fields_help=lambda model: [("name", "Name", "The name")],
        )

    def test_version_group(self):
        self.assertEqual(rst_help.version_group(10), "v10")
        self.assertEqual(rst_help.version_group(12), "v11_14")
        self.assertEqual(rst_help.version_group(15), "v15")
        self.assertEqual(rst_help.version_group(16), "v16_20")
        self.assertEqual(rst_help.version_group(21), "v16_20")
        self.assertEqual(rst_help.version_group(8), "v10")

    def test_split_lang(self):
        self.assertEqual(rst_help.split_lang("a.it_IT.rst"), ("a.rst", "it_IT"))
        self.assertEqual(rst_help.split_lang("a.rst"), ("a.rst", "en_US"))

    def test_sources_and_checksum(self):
        sources = rst_help.list_sources(self.help_dir, "v10")
        self.assertIn("v10", sources["intro.rst"])
        sources = rst_help.list_sources(self.help_dir, "v16_20")
        self.assertIn("common", sources["intro.rst"])
        before = rst_help.checksum(self.help_dir, "v16_20")
        self.assertEqual(before, rst_help.checksum(self.help_dir, "v16_20"))
        self.assertNotEqual(before, rst_help.checksum(self.help_dir, "v10"))
        self._write("v16_20/new.rst", "x\n")
        self.assertNotEqual(before, rst_help.checksum(self.help_dir, "v16_20"))

    def test_page_directives(self):
        doc = self._parse()
        self.assertEqual(doc.wch_page["name"], "partner")
        self.assertEqual(doc.wch_page["model"], "res.partner")
        self.assertEqual(
            doc.wch_page["view"], "base.view_partner_form,base.view_partner_tree"
        )
        self.assertEqual(doc.wch_page["view_type"], "form")
        self.assertEqual(rst_help.page_title(doc, doc.wch_page), "Partner")
        html = rst_help.to_html(doc)
        self.assertIn("<strong>intro</strong>", html)
        self.assertIn('data-field="name"', html)
        self.assertIn('data-tour="my_tour"', html)
        self.assertIn("wch-question", html)
        self.assertIn("The name", html)

    def test_include_group_and_lang(self):
        self.assertIn("Intro for 10", rst_help.to_html(self._parse(group="v10")))
        html = rst_help.to_html(self._parse(lang="it_IT"))
        self.assertIn("Introduzione comune", html)

    def test_include_missing(self):
        doc = rst_help.parse(
            ".. help-include:: none.rst\n", "x", self.help_dir, "v16_20"
        )
        self.assertNotIn("help-include", rst_help.to_html(doc))

    def test_inherit(self):
        inherit = rst_help.parse(
            ".. help-inherit:: a.partner\n   :section: usage\n   :position: after"
            "\n\n   Added\n   -----\n\n   extra text\n",
            "i",
            self.help_dir,
            "v16_20",
        ).wch_inherits
        self.assertEqual(len(inherit), 1)
        self.assertEqual(inherit[0]["target"], "a.partner")
        cases = {
            "after": lambda h: h.index("Usage")
            < h.index("extra text")
            < h.index("Other"),
            "before": lambda h: h.index("extra text") < h.index("Usage"),
            "replace": lambda h: "extra text" in h and "Fill" not in h,
            "remove": lambda h: "Fill" not in h and "extra text" not in h,
        }
        for position, check in cases.items():
            doc = self._parse()
            ok = rst_help.apply_inherit(
                doc,
                dict(inherit[0], position=position),
                self.help_dir,
                "v16_20",
                "en_US",
            )
            self.assertTrue(ok)
            self.assertTrue(check(rst_help.to_html(doc)), position)
        doc = self._parse()
        self.assertFalse(
            rst_help.apply_inherit(
                doc,
                dict(inherit[0], section="nothing"),
                self.help_dir,
                "v16_20",
                "en_US",
            )
        )
        rst_help.apply_inherit(
            doc, dict(inherit[0], section=""), self.help_dir, "v16_20", "en_US"
        )
        self.assertTrue(rst_help.to_html(doc).strip().endswith("</div>"))
        self.assertIn("extra text", rst_help.to_html(doc))

    def test_sections(self):
        sections = rst_help.extract_sections(self._parse())
        labels = [s["label"] for s in sections]
        self.assertIn("usage", labels)
        usage = [s for s in sections if s["label"] == "usage" and not s["question"]]
        self.assertNotIn("<a", usage[0]["text"])
        self.assertIn("Fill Name as <first>.<last>", usage[0]["text"])
        questions = [s["question"] for s in sections if s["question"]]
        self.assertEqual(questions, ["How to add a tag?", "Name"])

    def test_html_page(self):
        body = html_page.render("T<", "<p>x</p>", lang="it_IT", warning=True)
        self.assertIn("T&lt;", body)
        self.assertIn("Segui Odoo", body)
        self.assertIn("wch-warning", body)
        self.assertNotIn("<button", body)
        self.assertEqual(html_page.ASK_ENABLED, "wch_ask" in body)
        self.assertRegex(body, r"help_window\.css\?v=[0-9]+")
        body = html_page.render_auto(
            "P", [("name", "Name", "a<b")], model="res.partner"
        )
        self.assertIn('data-field="name"', body)
        self.assertIn("a&lt;b", body)
