# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request

from ..lib import html_page


class ContextHelp(http.Controller):
    def _lang(self, lang=None):
        return lang or request.env.context.get("lang") or request.env.user.lang

    @http.route("/web_context_help/lookup", type="json", auth="user")
    def lookup(self, model=None, view_type=None, view_id=None, lang=None, **kw):
        lang = self._lang(lang)
        Page = request.env["context.help.page"]
        page = Page.lookup(model=model, view_type=view_type, view_id=view_id, lang=lang)
        if page:
            return {"url": Page.page_url(page.key, lang), "key": page.key}
        if model and model in request.env:
            return {"url": "/web_context_help/auto/%s?lang=%s" % (model, lang)}
        return {"url": False}

    @http.route("/web_context_help/page/<string:key>", type="http", auth="user")
    def page(self, key, lang=None, **kw):
        lang = self._lang(lang)
        page = request.env["context.help.page"].get_page(key, lang)
        if not page:
            raise NotFound()
        body = html_page.render(
            page.name,
            page.html or "",
            lang=lang,
            page_key=page.key,
            model=page.model or "",
            warning=page.source_changed
            and request.env.user.has_group("base.group_system"),
        )
        return request.make_response(
            body, headers=[("Content-Type", "text/html; charset=utf-8")]
        )

    @http.route("/web_context_help/auto/<string:model>", type="http", auth="user")
    def auto(self, model, lang=None, **kw):
        lang = self._lang(lang)
        if model not in request.env:
            raise NotFound()
        Page = request.env["context.help.page"].with_context(lang=lang)
        title = (
            request.env["ir.model"]
            .with_context(lang=lang)
            .search([("model", "=", model)], limit=1)
            .name
        )
        body = html_page.render_auto(
            title or model, Page.fields_help(model), lang=lang, model=model
        )
        return request.make_response(
            body, headers=[("Content-Type", "text/html; charset=utf-8")]
        )

    @http.route("/web_context_help/ask", type="json", auth="user")
    def ask(self, question=None, context=None, **kw):
        context = dict(context or {})
        context.setdefault("lang", self._lang())
        return request.env["context.help.page"].ask(question, context)
