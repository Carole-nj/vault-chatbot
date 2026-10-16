/*
 * Vault Electronics chat widget. One <script> tag, no dependencies.
 *
 *   <script src="https://api.vaultelectronics.co.ke/widget/vault-chatbot.js"
 *           data-api="https://api.vaultelectronics.co.ke" defer></script>
 *
 * Optional attributes: data-color="#0b3d5c"  data-title="Vault Assistant"
 */
(function () {
  "use strict";
  if (window.__vaultChatLoaded) return;
  window.__vaultChatLoaded = true;

  var script = document.currentScript || document.querySelector("script[data-api]");
  var API = ((script && script.getAttribute("data-api")) || "").replace(/\/$/, "");
  var COLOR = (script && script.getAttribute("data-color")) || "#0b3d5c";
  var TITLE = (script && script.getAttribute("data-title")) || "Vault Electronics Assistant";
  var CHIPS = ["Products", "Request a demo", "Pricing", "Contact us"];
  var CHIP_QUERIES = {
    "Products": "What products do you offer?",
    "Request a demo": "I would like a demo",
    "Pricing": "What are your prices?",
    "Contact us": "How can I contact you?"
  };

  var sid = null;
  try { sid = localStorage.getItem("vault_chat_sid"); } catch (e) {}
  var busy = false;

  var css = [
    ".vc-root{position:fixed;right:20px;bottom:20px;z-index:2147483000;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}",
    ".vc-bubble{width:58px;height:58px;border-radius:50%;border:0;background:" + COLOR + ";color:#fff;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.3);display:flex;align-items:center;justify-content:center}",
    ".vc-bubble svg{width:28px;height:28px;fill:#fff}",
    ".vc-panel{display:none;flex-direction:column;position:absolute;right:0;bottom:72px;width:370px;max-width:calc(100vw - 24px);height:540px;max-height:calc(100vh - 110px);background:#fff;border-radius:14px;box-shadow:0 8px 30px rgba(0,0,0,.28);overflow:hidden}",
    ".vc-open .vc-panel{display:flex}",
    ".vc-head{background:" + COLOR + ";color:#fff;padding:14px 16px;display:flex;align-items:center;justify-content:space-between}",
    ".vc-head b{font-size:15px}.vc-head small{display:block;opacity:.85;font-size:11px;margin-top:2px}",
    ".vc-x{background:none;border:0;color:#fff;font-size:22px;cursor:pointer;line-height:1}",
    ".vc-msgs{flex:1;overflow-y:auto;padding:14px;background:#f4f6f8}",
    ".vc-m{max-width:84%;margin:0 0 10px;padding:9px 12px;border-radius:12px;font-size:14px;line-height:1.4;white-space:pre-wrap;word-wrap:break-word}",
    ".vc-bot{background:#fff;color:#1b1f23;border:1px solid #e3e7eb;border-bottom-left-radius:3px}",
    ".vc-user{background:" + COLOR + ";color:#fff;margin-left:auto;border-bottom-right-radius:3px}",
    ".vc-fb{margin:-4px 0 10px 4px;font-size:12px}",
    ".vc-fb button{background:none;border:1px solid #cfd6dd;border-radius:12px;cursor:pointer;margin-right:6px;padding:2px 8px}",
    ".vc-fb button:disabled{opacity:.5;cursor:default}",
    ".vc-typing{display:none;padding:0 14px 8px;background:#f4f6f8}",
    ".vc-typing span{display:inline-block;width:7px;height:7px;margin-right:4px;background:#9aa5b1;border-radius:50%;animation:vcb 1s infinite}",
    ".vc-typing span:nth-child(2){animation-delay:.15s}.vc-typing span:nth-child(3){animation-delay:.3s}",
    "@keyframes vcb{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}",
    ".vc-chips{padding:0 14px 10px;background:#f4f6f8}",
    ".vc-chips button{border:1px solid " + COLOR + ";color:" + COLOR + ";background:#fff;border-radius:16px;padding:5px 11px;margin:0 6px 6px 0;font-size:12.5px;cursor:pointer}",
    ".vc-form{display:flex;border-top:1px solid #e3e7eb;background:#fff}",
    ".vc-form input{flex:1;border:0;padding:14px;font-size:14px;outline:none;min-width:0}",
    ".vc-form button{border:0;background:" + COLOR + ";color:#fff;padding:0 18px;cursor:pointer;font-size:14px}",
    ".vc-form button:disabled{opacity:.6}",
    "@media(max-width:480px){.vc-root{right:12px;bottom:12px}.vc-panel{width:calc(100vw - 24px);height:calc(100vh - 100px)}}"
  ].join("\n");
  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text; // textContent: never interprets HTML
    return n;
  }

  var root = el("div", "vc-root");
  var bubble = el("button", "vc-bubble");
  bubble.setAttribute("aria-label", "Open chat");
  bubble.innerHTML = '<svg viewBox="0 0 24 24"><path d="M4 4h16a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H8l-5 4V6a2 2 0 0 1 1-2z"/></svg>';
  var panel = el("div", "vc-panel");
  var head = el("div", "vc-head");
  var ht = el("div");
  ht.appendChild(el("b", null, TITLE));
  ht.appendChild(el("small", null, "Technology Solutions That Work"));
  var close = el("button", "vc-x", "×");
  close.setAttribute("aria-label", "Close chat");
  head.appendChild(ht); head.appendChild(close);
  var msgs = el("div", "vc-msgs");
  msgs.setAttribute("aria-live", "polite");
  var typing = el("div", "vc-typing");
  typing.innerHTML = "<span></span><span></span><span></span>";
  var chips = el("div", "vc-chips");
  var form = el("form", "vc-form");
  var input = el("input");
  input.type = "text"; input.maxLength = 500; input.placeholder = "Type your question..."; input.setAttribute("aria-label", "Your message");
  var send = el("button", null, "Send");
  send.type = "submit";
  form.appendChild(input); form.appendChild(send);
  panel.appendChild(head); panel.appendChild(msgs); panel.appendChild(typing); panel.appendChild(chips); panel.appendChild(form);
  root.appendChild(panel); root.appendChild(bubble);
  document.body.appendChild(root);

  CHIPS.forEach(function (c) {
    var b = el("button", null, c);
    b.type = "button";
    b.onclick = function () { chips.style.display = "none"; ask(CHIP_QUERIES[c]); };
    chips.appendChild(b);
  });

  function scroll() { msgs.scrollTop = msgs.scrollHeight; }
  function addMsg(text, who) { var m = el("div", "vc-m " + (who === "user" ? "vc-user" : "vc-bot"), text); msgs.appendChild(m); scroll(); return m; }

  function addFeedback(messageId) {
    var box = el("div", "vc-fb");
    [["👍", 1], ["👎", -1]].forEach(function (p) {
      var b = el("button", null, p[0]);
      b.type = "button";
      b.setAttribute("aria-label", p[1] === 1 ? "Helpful" : "Not helpful");
      b.onclick = function () {
        Array.prototype.forEach.call(box.children, function (x) { x.disabled = true; });
        post("/feedback", { message_id: messageId, rating: p[1] }).catch(function () {});
      };
      box.appendChild(b);
    });
    msgs.appendChild(box); scroll();
  }

  function post(path, body) {
    return fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "ngrok-skip-browser-warning": "1" },
      body: JSON.stringify(body)
    }).then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); });
  }

  function ask(text) {
    text = (text || "").trim();
    if (!text || busy) return;
    busy = true; send.disabled = true;
    addMsg(text, "user");
    typing.style.display = "block"; scroll();
    post("/chat", { message: text, session_id: sid, page_url: location.href })
      .then(function (d) {
        sid = d.session_id;
        try { localStorage.setItem("vault_chat_sid", sid); } catch (e) {}
        addMsg(d.response, "bot");
        addFeedback(d.message_id);
      })
      .catch(function () {
        addMsg("Sorry, I'm having trouble connecting right now. Please call us on +254 762 139 352.", "bot");
      })
      .then(function () { typing.style.display = "none"; busy = false; send.disabled = false; input.focus(); });
  }

  form.addEventListener("submit", function (e) { e.preventDefault(); var v = input.value; input.value = ""; chips.style.display = "none"; ask(v); });

  var greeted = false;
  function toggle(open) {
    var on = open === undefined ? !root.classList.contains("vc-open") : open;
    root.classList.toggle("vc-open", on);
    if (on && !greeted) {
      greeted = true;
      addMsg("Hello! Welcome to Vault Electronics. How can I help you today?", "bot");
    }
    if (on) input.focus();
  }
  bubble.onclick = function () { toggle(); };
  close.onclick = function () { toggle(false); };
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") toggle(false); });
})();
