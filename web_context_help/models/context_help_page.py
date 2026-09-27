# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
import logging
import os
import re

from odoo import api, fields, models, release
from odoo.modules.module import get_module_path

from ..lib import rst_help

_logger = logging.getLogger(__name__)

RE_WORD = re.compile(r"\w{3,}", re.UNICODE)
# The web client says "list", arch and actions say "tree"
VIEW_TYPE_ALIASES = {"list": ("list", "tree"), "tree": ("list", "tree")}


class ContextHelpSource(models.Model):
    _name = "context.help.source"
    _description = "Context help source checksum"

    module = fields.Char(required=True, index=True)
    checksum = fields.Char()

    _sql_constraints = [
        ("module_uniq", "unique(module)", "Module must be unique"),
    ]


class ContextHelpSection(models.Model):
    _name = "context.help.section"
    _description = "Context help section"
    _order = "page_id, sequence, id"

    page_id = fields.Many2one(
        "context.help.page", required=True, index=True, ondelete="cascade"
    )
    sequence = fields.Integer()
    label = fields.Char()
    title = fields.Char()
    text = fields.Text()
    question = fields.Char()


class ContextHelpPage(models.Model):
    _name = "context.help.page"
    _description = "Context help page"
    _order = "key, lang"

    key = fields.Char(required=True, index=True, help="<module>.<name>")
    name = fields.Char("Title", required=True)
    lang = fields.Char(required=True, default=rst_help.DEFAULT_LANG, index=True)
    module = fields.Char(index=True)
    source_file = fields.Char(readonly=True)
    model = fields.Char(index=True)
    view_xmlid = fields.Char(
        "Views", help="Comma separated xmlids of the views this page explains"
    )
    view_type = fields.Char()
    source_html = fields.Html(sanitize=False, readonly=True)
    html = fields.Html("Content", sanitize=False)
    edited = fields.Boolean(
        readonly=True, help="Content was changed by an administrator"
    )
    source_changed = fields.Boolean(
        readonly=True,
        help="Source changed after the content was edited by an administrator",
    )
    section_ids = fields.One2many("context.help.section", "page_id", "Sections")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("key_lang_uniq", "unique(key, lang)", "Page key must be unique per language"),
    ]

    # ------------------------------------------------------------------
    # Admin editing
    # ------------------------------------------------------------------
    @api.multi
    def write(self, vals):
        if "html" in vals and not self.env.context.get("wch_sync"):
            vals = dict(vals, edited=True)
        return super(ContextHelpPage, self).write(vals)

    @api.multi
    def action_reset_to_source(self):
        for page in self:
            page.with_context(wch_sync=True).write(
                {"html": page.source_html, "edited": False, "source_changed": False}
            )
        return True

    @api.multi
    def action_source_seen(self):
        return self.write({"source_changed": False})

    @api.multi
    def action_rebuild(self):
        self.sudo().sync_sources(force=True)
        return True

    @api.multi
    def action_open(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_url",
            "url": self.page_url(self.key, self.lang),
            "target": "new",
        }

    @api.model
    def page_url(self, key, lang=None):
        url = "/web_context_help/page/%s" % key
        return "%s?lang=%s" % (url, lang) if lang else url

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------
    @api.model
    def _wch_view_xmlid(self, view_id):
        if not view_id:
            return False
        data = self.env["ir.model.data"].sudo().search(
            [("model", "=", "ir.ui.view"), ("res_id", "=", int(view_id))], limit=1
        )
        return "%s.%s" % (data.module, data.name) if data else False

    @api.model
    def lookup(self, model=None, view_type=None, view_id=None, lang=None):
        """Return the page matching the Odoo context, or an empty recordset.

        Order: view xmlid -> model + view_type -> model."""
        lang = lang or self.env.context.get("lang") or rst_help.DEFAULT_LANG
        xmlid = self._wch_view_xmlid(view_id)
        pages = self.browse()
        if xmlid:
            pages = self.search([("view_xmlid", "ilike", xmlid)]).filtered(
                lambda p: xmlid in (p.view_xmlid or "").split(",")
            )
        if not pages and model and view_type:
            types = VIEW_TYPE_ALIASES.get(view_type, (view_type,))
            pages = self.search([("model", "=", model), ("view_type", "in", types)])
        if not pages and model:
            pages = self.search(
                [("model", "=", model), ("view_type", "in", (False, ""))]
            )
        if not pages:
            return pages
        return self._wch_best_lang(pages, lang)

    @api.model
    def _wch_best_lang(self, pages, lang):
        for code in (lang, rst_help.DEFAULT_LANG):
            found = pages.filtered(lambda p: p.lang == code)
            if found:
                return found[0]
        return pages[0]

    @api.model
    def get_page(self, key, lang=None):
        lang = lang or self.env.context.get("lang") or rst_help.DEFAULT_LANG
        pages = self.search([("key", "=", key)])
        return self._wch_best_lang(pages, lang) if pages else pages

    @api.model
    def _wch_with_lang(self, lang):
        """Self in lang when installed: Odoo 17+ rejects any other code"""
        if lang in dict(self.env["res.lang"].get_installed()):
            return self.with_context(lang=lang)
        return self

    @api.model
    def fields_help(self, model):
        """[(name, string, help)] of the fields of model having a help"""
        if model not in self.env:
            return []
        info = self.env[model].fields_get(attributes=["string", "help"])
        return sorted(
            (name, vals.get("string") or name, vals["help"])
            for name, vals in info.items()
            if vals.get("help")
        )

    # ------------------------------------------------------------------
    # Ask
    # ------------------------------------------------------------------
    @api.model
    def _wch_ask_providers(self):
        """Ordered method names answering ``(question, context)``.

        Override to add a provider: the first one returning results wins."""
        return ["_wch_ask_fulltext"]

    @api.model
    def ask(self, question, context=None):
        context = context or {}
        question = (question or "").strip()
        if not question:
            return {"results": [], "provider": False}
        results, provider = [], False
        for method in self._wch_ask_providers():
            results = getattr(self, method)(question, context)
            if results:
                provider = method
                break
        self.env["context.help.question"].sudo().create(
            {
                "question": question[:1024],
                "model": context.get("model") or False,
                "page_key": context.get("page_key") or False,
                "found": bool(results),
                "provider": provider or False,
                "answer_page_id": results[0]["page_id"] if results else False,
            }
        )
        return {"results": results, "provider": provider}

    @api.model
    def _wch_ask_fulltext(self, question, context, limit=5):
        words = set(w.lower() for w in RE_WORD.findall(question))
        if not words:
            return []
        lang = context.get("lang") or self.env.context.get("lang") or rst_help.DEFAULT_LANG
        domain = [("page_id.active", "=", True), ("page_id.lang", "in", (lang, rst_help.DEFAULT_LANG))]
        scored = []
        for section in self.env["context.help.section"].search(domain):
            title = (section.title or "").lower()
            text = (section.text or "").lower()
            score = sum(
                3 * (w in title) + (w in text) + 2 * (w in (section.question or "").lower())
                for w in words
            )
            if context.get("model") and section.page_id.model == context["model"]:
                score += 1
            if score > len(words) // 2:
                scored.append((score, section))
        scored.sort(key=lambda x: (-x[0], x[1].id))
        results, seen = [], set()
        for score, section in scored:
            page = section.page_id
            if (page.key, section.label) in seen:
                continue
            seen.add((page.key, section.label))
            results.append(
                {
                    "page_id": page.id,
                    "page_key": page.key,
                    "page_title": page.name,
                    "title": section.title,
                    "snippet": (section.text or "")[:300],
                    "url": "%s#%s" % (self.page_url(page.key, page.lang), section.label),
                    "score": score,
                }
            )
            if len(results) >= limit:
                break
        return results

    # ------------------------------------------------------------------
    # Build from RST sources
    # ------------------------------------------------------------------
    def _register_hook(self):
        res = super(ContextHelpPage, self)._register_hook()
        try:
            with self.env.cr.savepoint():
                self.sudo().sync_sources()
        except Exception:  # pragma: no cover
            _logger.exception("web_context_help: help sources not synchronized")
        return res

    @api.model
    def _wch_group(self):
        return rst_help.version_group(release.version_info[0])

    @api.model
    def _wch_modules(self):
        """Installed modules having help sources, in dependency order"""
        mods = self.env["ir.module.module"].search(
            [("state", "in", ("installed", "to upgrade"))]
        )
        deps = {m.name: set(m.dependencies_id.mapped("name")) for m in mods}
        ordered, done = [], set()

        def visit(name, stack):
            if name in done or name not in deps or name in stack:
                return
            for dep in sorted(deps[name]):
                visit(dep, stack | {name})
            done.add(name)
            ordered.append(name)

        for name in sorted(deps):
            visit(name, set())
        result = []
        for name in ordered:
            path = get_module_path(name)
            help_dir = path and os.path.join(path, "help")
            if help_dir and os.path.isdir(help_dir):
                result.append((name, help_dir))
        return result

    @api.model
    def sync_sources(self, force=False):
        """Rebuild the pages when any help source checksum changed"""
        group = self._wch_group()
        modules = self._wch_modules()
        checksums = {name: rst_help.checksum(path, group) for name, path in modules}
        Source = self.env["context.help.source"]
        stored = {s.module: s for s in Source.search([])}
        if not force and checksums == {m: s.checksum for m, s in stored.items()}:
            return False
        _logger.info("web_context_help: rebuilding help pages")
        self._wch_rebuild(modules, group)
        for name, value in checksums.items():
            if name in stored:
                if stored[name].checksum != value:
                    stored[name].checksum = value
            else:
                Source.create({"module": name, "checksum": value})
        for name, rec in stored.items():
            if name not in checksums:
                rec.unlink()
        return True

    @api.model
    def _wch_parse_module(self, module, help_dir, group):
        """Return (pages, inherits) parsed from the sources of one module"""
        pages, inherits = [], []
        for filename, path in sorted(rst_help.list_sources(help_dir, group).items()):
            base, lang = rst_help.split_lang(filename)
            try:
                doc = rst_help.parse_file(
                    path,
                    help_dir,
                    group,
                    lang,
                    fields_help=self._wch_with_lang(lang).fields_help,
                )
            except Exception as e:
                _logger.warning("web_context_help: %s not parsed: %s", path, e)
                continue
            for inherit in doc.wch_inherits:
                inherits.append(dict(inherit, module=module, base=base, lang=lang))
            if doc.wch_page:
                pages.append(
                    {
                        "doc": doc,
                        "module": module,
                        "help_dir": help_dir,
                        "path": path,
                        "base": base,
                        "lang": lang,
                        "page": doc.wch_page,
                    }
                )
        return pages, inherits

    @api.model
    def _wch_inherits_for(self, inherits, key, lang):
        """Inherits of a page in lang; a source without twin applies to all"""
        result = []
        sources = {}
        for inherit in inherits:
            if inherit["target"] != key:
                continue
            sources.setdefault((inherit["module"], inherit["base"]), []).append(inherit)
        for dummy, items in sources.items():
            langs = set(i["lang"] for i in items)
            use = lang if lang in langs else rst_help.DEFAULT_LANG
            result.extend(i for i in items if i["lang"] == use)
        return result

    @api.model
    def _wch_rebuild(self, modules, group):
        order = {name: seq for seq, (name, dummy) in enumerate(modules)}
        pages, inherits = [], []
        for module, help_dir in modules:
            p, i = self._wch_parse_module(module, help_dir, group)
            pages.extend(p)
            inherits.extend(i)
        inherits.sort(key=lambda i: order.get(i["module"], 0))
        built = {}
        for item in pages:
            key = "%s.%s" % (item["module"], item["page"]["name"])
            doc = item["doc"]
            for inherit in self._wch_inherits_for(inherits, key, item["lang"]):
                ok = rst_help.apply_inherit(
                    doc,
                    inherit,
                    item["help_dir"],
                    group,
                    item["lang"],
                    self._wch_with_lang(item["lang"]).fields_help,
                )
                if not ok:
                    _logger.warning(
                        "web_context_help: %s inherit from %s: section %s not found",
                        key,
                        inherit["module"],
                        inherit["section"],
                    )
            page = item["page"]
            built[(key, item["lang"])] = {
                "vals": {
                    "key": key,
                    "lang": item["lang"],
                    "name": rst_help.page_title(doc, page),
                    "module": item["module"],
                    "source_file": os.path.relpath(
                        item["path"], os.path.dirname(item["help_dir"])
                    ),
                    "model": page["model"] or False,
                    "view_xmlid": page["view"] or False,
                    "view_type": page["view_type"] or False,
                    "active": True,
                },
                "html": rst_help.to_html(doc),
                "sections": rst_help.extract_sections(doc),
            }
        self._wch_store(built)

    @api.model
    def _wch_store(self, built):
        Page = self.with_context(wch_sync=True, active_test=False)
        existing = {(p.key, p.lang): p for p in Page.search([])}
        for ident, data in built.items():
            vals = dict(data["vals"])
            page = existing.pop(ident, None)
            html = data["html"]
            if page is None:
                vals.update(source_html=html, html=html)
                page = Page.create(vals)
            else:
                if page.source_html != html:
                    vals["source_html"] = html
                    if page.edited:
                        vals["source_changed"] = True
                    else:
                        vals["html"] = html
                page.write(vals)
                page.section_ids.unlink()
            for seq, section in enumerate(data["sections"]):
                self.env["context.help.section"].create(
                    dict(section, page_id=page.id, sequence=seq)
                )
        for page in existing.values():
            if page.edited:
                page.active = False
            else:
                page.unlink()


class ContextHelpQuestion(models.Model):
    _name = "context.help.question"
    _description = "Context help question log"
    _order = "id desc"

    question = fields.Char(required=True)
    model = fields.Char()
    page_key = fields.Char()
    user_id = fields.Many2one("res.users", default=lambda self: self.env.uid)
    found = fields.Boolean()
    provider = fields.Char()
    answer_page_id = fields.Many2one("context.help.page", ondelete="set null")

