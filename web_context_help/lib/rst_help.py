# -*- coding: utf-8 -*-
#
# Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
#
# License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
#
"""Context help RST engine: pure docutils, no Odoo import, Python 2.7 and 3.

Help sources live in ``<module>/help/``: ``common/`` plus one directory per
group of Odoo versions (``v10``, ``v11_14``, ``v15``, ``v16_20``). A file in
the group directory overrides the file with the same name in ``common/``.
Italian twins carry the iso code before the extension (``page.it_IT.rst``).

Custom directives::

    .. help-page:: name                 page key becomes <module>.<name>
       :title: Title
       :model: res.partner
       :view: base.view_partner_form, base.view_partner_tree
       :view-type: form

    .. help-include:: file.rst          group dir, then common/ fallback

    .. help-inherit:: module.name       change a page of another module
       :section: label                  section id or name
       :position: after                 before | after | replace | remove

       RST content

    .. help-question:: Question?        FAQ entry, content is the answer
    .. help-question::                  :auto: questions from fields help
       :auto:
       :model: res.partner

Roles: :field:`name` (highlight field in Odoo tab), :tour:`name` (run tour).
"""
from __future__ import unicode_literals

import hashlib
import io
import logging
import os
import re

from docutils import core, io as docio, nodes
from docutils.parsers.rst import Directive, directives, roles
from docutils.readers.doctree import Reader as DoctreeReader

_logger = logging.getLogger(__name__)

VERSION_GROUPS = (
    (10, 10, "v10"),
    (11, 14, "v11_14"),
    (15, 15, "v15"),
    (16, 20, "v16_20"),
)
COMMON = "common"
DEFAULT_LANG = "en_US"
POSITIONS = ("before", "after", "replace", "remove")
RE_LANG = re.compile(r"^(?P<base>.+?)\.(?P<lang>[a-z]{2}_[A-Z]{2})\.rst$")

try:  # pragma: no cover
    from markupsafe import escape
except ImportError:  # pragma: no cover
    from cgi import escape


def version_group(major):
    for lo, hi, group in VERSION_GROUPS:
        if lo <= major <= hi:
            return group
    return VERSION_GROUPS[-1][2] if major > 20 else VERSION_GROUPS[0][2]


def split_lang(filename):
    """``page.it_IT.rst`` -> (``page.rst``, ``it_IT``)"""
    x = RE_LANG.match(filename)
    if x:
        return x.group("base") + ".rst", x.group("lang")
    return filename, DEFAULT_LANG


def list_sources(help_dir, group):
    """Return {filename: fullpath} of the RST sources visible for group"""
    sources = {}
    for subdir in (COMMON, group):
        path = os.path.join(help_dir, subdir)
        if not os.path.isdir(path):
            continue
        for fn in sorted(os.listdir(path)):
            if fn.endswith(".rst"):
                sources[fn] = os.path.join(path, fn)
    return sources


def checksum(help_dir, group):
    sha = hashlib.sha1(group.encode("utf-8"))
    for fn, path in sorted(list_sources(help_dir, group).items()):
        sha.update(fn.encode("utf-8"))
        with open(path, "rb") as fd:
            sha.update(fd.read())
    return sha.hexdigest()


def resolve_include(help_dir, group, name, lang=DEFAULT_LANG):
    names = [name]
    if lang != DEFAULT_LANG and name.endswith(".rst"):
        names.insert(0, "%s.%s.rst" % (name[:-4], lang))
    for fn in names:
        for subdir in (group, COMMON):
            path = os.path.join(help_dir, subdir, fn)
            if os.path.isfile(path):
                return path
    return False


def read_text(path):
    with io.open(path, "r", encoding="utf-8") as fd:
        return fd.read()


class _LogStream(object):
    def write(self, text):
        _logger.debug(text.strip())


def _settings(help_dir, group, lang, fields_help):
    return {
        "doctitle_xform": False,
        "sectsubtitle_xform": False,
        "report_level": 3,
        "halt_level": 5,
        "warning_stream": _LogStream(),
        "input_encoding": "unicode",
        "output_encoding": "unicode",
        "file_insertion_enabled": False,
        "raw_enabled": True,
        "embed_stylesheet": False,
        "stylesheet_path": "",
        "initial_header_level": 2,
        "wch_help_dir": help_dir,
        "wch_group": group,
        "wch_lang": lang,
        "wch_fields_help": fields_help,
    }


def _findall(node, condition):
    """docutils >= 0.18 obsoletes traverse() by findall()"""
    if hasattr(node, "findall"):
        return list(node.findall(condition))
    return node.traverse(condition)  # pragma: no cover


def _store(document, key, default):
    if not hasattr(document, key):
        setattr(document, key, default)
    return getattr(document, key)


class HelpPage(Directive):
    required_arguments = 1
    has_content = False
    option_spec = {
        "title": directives.unchanged,
        "model": directives.unchanged,
        "view": directives.unchanged,
        "view-type": directives.unchanged,
    }

    def run(self):
        page = {
            "name": self.arguments[0].strip(),
            "title": self.options.get("title", ""),
            "model": self.options.get("model", ""),
            "view": ",".join(
                x.strip() for x in self.options.get("view", "").split(",") if x.strip()
            ),
            "view_type": self.options.get("view-type", ""),
        }
        self.state.document.wch_page = page
        return []


class HelpInclude(Directive):
    required_arguments = 1
    has_content = False

    def run(self):
        settings = self.state.document.settings
        path = resolve_include(
            settings.wch_help_dir,
            settings.wch_group,
            self.arguments[0].strip(),
            settings.wch_lang,
        )
        if not path:
            raise self.error("help-include: file %s not found" % self.arguments[0])
        stack = _store(self.state.document, "wch_include_stack", [])
        if path in stack or len(stack) > 10:
            raise self.error("help-include: recursive include of %s" % path)
        stack.append(path)
        lines = read_text(path).splitlines()
        self.state_machine.insert_input(lines, path)
        return []


class HelpInherit(Directive):
    required_arguments = 1
    has_content = True
    option_spec = {
        "section": directives.unchanged,
        "position": lambda arg: directives.choice(arg, POSITIONS),
    }

    def run(self):
        position = self.options.get("position", "after")
        section = self.options.get("section", "")
        if not section and position in ("replace", "remove"):
            raise self.error("help-inherit: :section: required by %s" % position)
        _store(self.state.document, "wch_inherits", []).append(
            {
                "target": self.arguments[0].strip(),
                "section": section,
                "position": position,
                "content": "\n".join(self.content),
            }
        )
        return []


class HelpQuestion(Directive):
    optional_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {"auto": directives.flag, "model": directives.unchanged}

    def run(self):
        document = self.state.document
        if "auto" in self.options:
            model = self.options.get("model") or getattr(
                document, "wch_page", {}
            ).get("model")
            fields_help = document.settings.wch_fields_help
            if not model or not fields_help:
                return []
            return [
                self._question(label, [help_text])
                for (dummy, label, help_text) in fields_help(model)
            ]
        if not self.arguments:
            raise self.error("help-question: question text required")
        return [self._question(self.arguments[0], None)]

    def _question(self, question, answer):
        box = nodes.container(classes=["wch-question"])
        box["wch_question"] = question
        box += nodes.paragraph(question, question, classes=["wch-q"])
        body = nodes.container(classes=["wch-a"])
        if answer is None:
            self.state.nested_parse(self.content, self.content_offset, body)
        else:
            for text in answer:
                body += nodes.paragraph(text, text)
        box += body
        return box


def _data_role(kind):
    def role(name, rawtext, text, lineno, inliner, options=None, content=None):
        text = nodes.unescape(text)
        label, target = text, text
        x = re.match(r"^(.*?)\s*<([^<>]+)>$", text)
        if x:
            label, target = x.group(1), x.group(2)
        html = '<a href="#" class="wch-%s" data-%s="%s">%s</a>' % (
            kind,
            kind,
            escape(target),
            escape(label),
        )
        node = nodes.raw(rawtext, html, format="html")
        node["wch_label"] = label
        return [node], []

    return role


directives.register_directive("help-page", HelpPage)
directives.register_directive("help-include", HelpInclude)
directives.register_directive("help-inherit", HelpInherit)
directives.register_directive("help-question", HelpQuestion)
roles.register_local_role("field", _data_role("field"))
roles.register_local_role("tour", _data_role("tour"))


def parse(text, source_path, help_dir, group, lang=DEFAULT_LANG, fields_help=None):
    """Parse RST text; return the doctree.

    ``document.wch_page`` holds the help-page options (or None),
    ``document.wch_inherits`` the help-inherit instructions."""
    if isinstance(text, bytes):  # Python 2 str
        text = text.decode("utf-8")
    document = core.publish_doctree(
        text,
        source_path=source_path,
        settings_overrides=_settings(help_dir, group, lang, fields_help),
    )
    _store(document, "wch_page", None)
    _store(document, "wch_inherits", [])
    return document


def parse_file(path, help_dir, group, lang=DEFAULT_LANG, fields_help=None):
    return parse(read_text(path), path, help_dir, group, lang, fields_help)


def find_section(document, label):
    for node in _findall(document, nodes.section):
        if label in node["ids"] or label in node["names"]:
            return node
    return None


def apply_inherit(document, inherit, help_dir, group, lang, fields_help=None):
    """Apply one help-inherit instruction to a page doctree; return success"""
    position = inherit["position"]
    if inherit["section"]:
        target = find_section(document, inherit["section"])
        if target is None:
            return False
    else:
        target = None
    new_nodes = []
    if position != "remove":
        new_nodes = parse(
            inherit["content"], "<inherit>", help_dir, group, lang, fields_help
        ).children[:]
    if target is None:
        if position == "before":
            for node in reversed(new_nodes):
                document.insert(0, node)
        else:
            document.extend(new_nodes)
        return True
    parent = target.parent
    index = parent.index(target)
    if position == "remove":
        parent.remove(target)
    elif position == "replace":
        parent.remove(target)
        for node in reversed(new_nodes):
            parent.insert(index, node)
    elif position == "before":
        for node in reversed(new_nodes):
            parent.insert(index, node)
    else:
        for node in reversed(new_nodes):
            parent.insert(index + 1, node)
    return True


def to_html(document):
    """Render a doctree to an HTML fragment"""
    publisher = core.Publisher(
        reader=DoctreeReader(parser_name="null"),
        source=docio.DocTreeInput(document),
        destination_class=docio.StringOutput,
    )
    publisher.set_writer("html")
    publisher.process_programmatic_settings(
        None,
        {
            "output_encoding": "unicode",
            "embed_stylesheet": False,
            "stylesheet_path": "",
            "report_level": 5,
            "warning_stream": _LogStream(),
        },
        None,
    )
    publisher.set_destination(None, None)
    publisher.publish()
    return publisher.writer.parts["body"]


def page_title(document, page):
    if page and page.get("title"):
        return page["title"]
    for node in _findall(document, nodes.title):
        return node.astext()
    return page["name"] if page else ""


RE_AUTO_ID = re.compile(r"^id[0-9]+$")


def _label(section):
    named = set(nodes.make_id(x) for x in section["names"])
    ids = [x for x in section["ids"] if x in named]
    if ids:
        return ids[0]
    ids = [x for x in section["ids"] if not RE_AUTO_ID.match(x)]
    return (ids or section["ids"] or [""])[0]


def _plain(node):
    """Text of node; raw HTML of the roles gives its label only"""
    if isinstance(node, nodes.raw):
        return node.get("wch_label", "")
    if isinstance(node, nodes.Text):
        return node.astext()
    sep = "\n\n" if isinstance(node, (nodes.container, nodes.section)) else ""
    return sep.join(_plain(child) for child in node.children)


def extract_sections(document):
    """Return [{label, title, text, question}] used by the full-text search.

    Sections are flattened: the text of a section excludes its subsections.
    Each help-question is also returned as its own entry."""
    result = []
    for section in _findall(document, nodes.section):
        title = section.next_node(nodes.title)
        texts = [
            _plain(child)
            for child in section.children
            if not isinstance(child, (nodes.section, nodes.title))
        ]
        result.append(
            {
                "label": _label(section),
                "title": title.astext() if title else "",
                "text": "\n".join(texts),
                "question": "",
            }
        )
    for box in _findall(document, nodes.container):
        if box.get("wch_question"):
            section = box.parent
            while section is not None and not isinstance(section, nodes.section):
                section = section.parent
            answer = _plain(box.children[1]) if len(box.children) > 1 else ""
            result.append(
                {
                    "label": _label(section) if section is not None else "",
                    "title": box["wch_question"],
                    "text": answer,
                    "question": box["wch_question"],
                }
            )
    return result
