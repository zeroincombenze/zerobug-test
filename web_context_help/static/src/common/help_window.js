/* Copyright 2026 Zeroincombenze srls <https://www.zeroincombenze.it>
 * License LGPL-3.0-or-later (https://www.gnu.org/licenses/lgpl).
 *
 * Help window script: plain ES5, shared by every Odoo version.
 * Talks to the Odoo tab (window.opener) through postMessage.
 */
(function () {
    "use strict";
    var config = window.wchConfig || {};
    var labels = config.labels || {};
    var FOLLOW_KEY = "web_context_help.follow";

    function post(message) {
        if (window.opener && !window.opener.closed) {
            window.opener.postMessage(message, window.location.origin);
            window.opener.focus();
        }
    }

    function getFollow() {
        try {
            return window.localStorage.getItem(FOLLOW_KEY) !== "0";
        } catch (e) {
            return true;
        }
    }

    function setFollow(value) {
        try {
            window.localStorage.setItem(FOLLOW_KEY, value ? "1" : "0");
        } catch (e) {
            // storage unavailable: follow stays on
        }
        post({type: "wch_follow", value: value});
    }

    function onClick(ev) {
        var el = ev.target.closest ? ev.target.closest("a.wch-field, a.wch-tour") : null;
        if (!el) {
            return;
        }
        ev.preventDefault();
        if (el.classList.contains("wch-field")) {
            post({type: "wch_highlight", field: el.getAttribute("data-field")});
        } else {
            post({type: "wch_tour", tour: el.getAttribute("data-tour")});
        }
    }

    function text(tag, value, cls) {
        var el = document.createElement(tag);
        el.textContent = value;
        if (cls) {
            el.className = cls;
        }
        return el;
    }

    function showAnswers(results) {
        var box = document.getElementById("wch_answers");
        box.innerHTML = "";
        if (!results.length) {
            box.appendChild(text("p", labels.none || "No answer found", "wch-none"));
            return;
        }
        results.forEach(function (res) {
            var item = document.createElement("div");
            item.className = "wch-answer";
            var link = text("a", res.title || res.page_title);
            link.href = res.url;
            item.appendChild(link);
            if (res.page_title && res.page_title !== res.title) {
                item.appendChild(text("span", " — " + res.page_title, "wch-page"));
            }
            item.appendChild(text("p", res.snippet));
            box.appendChild(item);
        });
    }

    function ask(ev) {
        ev.preventDefault();
        var question = document.getElementById("wch_question").value;
        if (!question.trim()) {
            return;
        }
        var xhr = new XMLHttpRequest();
        xhr.open("POST", "/web_context_help/ask");
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.onload = function () {
            var data = JSON.parse(xhr.responseText);
            showAnswers((data.result && data.result.results) || []);
        };
        xhr.send(
            JSON.stringify({
                jsonrpc: "2.0",
                method: "call",
                params: {
                    question: question,
                    context: {
                        model: config.model,
                        page_key: config.page_key,
                        lang: config.lang,
                    },
                },
            })
        );
    }

    document.addEventListener("DOMContentLoaded", function () {
        var follow = document.getElementById("wch_follow");
        follow.checked = getFollow();
        follow.addEventListener("change", function () {
            setFollow(follow.checked);
        });
        var askForm = document.getElementById("wch_ask");
        if (askForm) {
            askForm.addEventListener("submit", ask);
        }
        document.addEventListener("click", onClick);
        post({type: "wch_ready", page_key: config.page_key});
    });
})();
