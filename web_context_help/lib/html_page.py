# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
"""Standalone HTML document of the help window; no QWeb, version independent"""
from __future__ import unicode_literals

import json
import os

try:  # pragma: no cover
    from markupsafe import escape
except ImportError:  # pragma: no cover
    from cgi import escape

STATIC = "/web_context_help/static/src/common"
# The question box is hidden until the ask feature is released
ASK_ENABLED = False
STATIC_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "src", "common"
)


def asset_version():
    """Cache buster: last change of the help window assets"""
    try:
        return int(
            max(
                os.path.getmtime(os.path.join(STATIC_DIR, fn))
                for fn in os.listdir(STATIC_DIR)
            )
        )
    except (OSError, ValueError):
        return 0


LABELS = {
    "en_US": {
        "follow": "Follow Odoo",
        "ask": "Ask a question",
        "none": "No answer found",
        "auto": "Fields of this form",
        "changed": "The original source has changed since this page was edited.",
    },
    "it_IT": {
        "follow": "Segui Odoo",
        "ask": "Fai una domanda",
        "none": "Nessuna risposta trovata",
        "auto": "Campi di questa maschera",
        "changed": "La sorgente originale è cambiata dopo la modifica di questa pagina.",
    },
}


def labels(lang):
    return LABELS.get(lang) or LABELS.get((lang or "")[:2] + "_IT") or LABELS["en_US"]


def render(title, body_html, lang="en_US", page_key="", model="", warning=False):
    tr = labels(lang)
    config = json.dumps(
        {"page_key": page_key, "model": model, "lang": lang, "labels": tr}
    ).replace("</", "<\\/")
    return """<!DOCTYPE html>
<html lang="%(lang)s">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>%(title)s</title>
<link rel="stylesheet" href="%(static)s/help_window.css?v=%(version)s"/>
</head>
<body class="wch-body">
<header class="wch-header">
  <label class="wch-follow"><input type="checkbox" id="wch_follow"/> %(follow)s</label>
%(ask_form)s</header>
%(answers)s%(warning)s<main class="wch-content">
%(body)s
</main>
<script>window.wchConfig = %(config)s;</script>
<script src="%(static)s/help_window.js?v=%(version)s"></script>
</body>
</html>
""" % {
        "lang": escape(lang.replace("_", "-")),
        "title": escape(title),
        "static": STATIC,
        "version": asset_version(),
        "follow": escape(tr["follow"]),
        "ask_form": (
            '  <form class="wch-ask" id="wch_ask">\n'
            '    <input type="search" id="wch_question" placeholder="%s"'
            ' autocomplete="off"/>\n'
            "  </form>\n" % escape(tr["ask"])
            if ASK_ENABLED
            else ""
        ),
        "answers": (
            '<div id="wch_answers" class="wch-answers"></div>\n'
            if ASK_ENABLED
            else ""
        ),
        "warning": (
            '<div class="wch-warning">%s</div>\n' % escape(tr["changed"])
            if warning
            else ""
        ),
        "body": body_html,
        "config": config,
    }


def render_auto(title, fields_help, lang="en_US", model=""):
    """Page built on the fly from the fields help of a model"""
    tr = labels(lang)
    rows = "\n".join(
        '<dt><a href="#" class="wch-field" data-field="%s">%s</a></dt><dd>%s</dd>'
        % (escape(name), escape(string), escape(text))
        for name, string, text in fields_help
    )
    body = '<h1>%s</h1>\n<h2>%s</h2>\n<dl class="wch-auto">\n%s\n</dl>' % (
        escape(title),
        escape(tr["auto"]),
        rows,
    )
    return render(title, body, lang=lang, model=model)
