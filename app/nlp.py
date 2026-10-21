"""Text preprocessing, FAQ search, intent classification and layered response logic."""
import json
import re
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

URL_RE = re.compile(r"https?://\S+|www\.\S+")
SYNONYMS = {
    "smartboard": "interactive panel",
    "smartboards": "interactive panel",
    "whiteboard": "interactive panel",
    "ifp": "interactive flat panel",
    "cameras": "camera",
    "quotation": "quote",
    "price": "price",
    "prices": "price",
}
YES = {"yes", "yeah", "yep", "ok", "okay", "sure", "please", "yes please", "y"}


def preprocess(text: str) -> str:
    """Shared by training and inference: it must stay identical in both."""
    t = text.lower().replace('"', " inch ")
    t = URL_RE.sub(" ", t)
    t = re.sub(r"[^a-z0-9\s']", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return " ".join(SYNONYMS.get(w, w) for w in t.split())


class ChatEngine:
    def __init__(self, base_dir, config):
        self.base = Path(base_dir)
        self.cfg = config
        self.kb_path = self.base / "data" / "knowledge_base.json"
        self.model = joblib.load(self.base / "models" / "intent_model.joblib")
        self.embedder = None
        if config.get("use_embeddings"):
            try:  # optional heavy dependency
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer(config.get("embedding_model", "BAAI/bge-small-en-v1.5"))
            except Exception:
                self.embedder = None
        self._kb_mtime = 0.0
        self._load_kb()

    # ---------- knowledge base (hot-reloads when staff edit the JSON) ----------
    def _load_kb(self):
        self._kb_mtime = self.kb_path.stat().st_mtime
        with open(self.kb_path, encoding="utf-8") as f:
            self.kb = json.load(f)
        texts, owners = [], []
        for i, faq in enumerate(self.kb.get("faqs", [])):
            for q in [faq["q"]] + faq.get("variants", []):
                texts.append(preprocess(q))
                owners.append(i)
        self.faq_owner = np.array(owners)
        self.vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.faq_matrix = self.vec.fit_transform(texts) if texts else None
        self.faq_emb = None
        if self.embedder is not None and texts:
            self.faq_emb = self.embedder.encode(texts, normalize_embeddings=True)

    def _maybe_reload(self):
        try:
            if self.kb_path.stat().st_mtime != self._kb_mtime:
                self._load_kb()
        except FileNotFoundError:
            pass

    # ---------- layers ----------
    def faq_search(self, clean: str):
        if self.faq_matrix is None or not clean:
            return None, 0.0
        sims = cosine_similarity(self.vec.transform([clean]), self.faq_matrix)[0]
        if self.faq_emb is not None:
            emb = self.faq_emb @ self.embedder.encode([clean], normalize_embeddings=True)[0]
            sims = 0.4 * sims + 0.6 * emb
        best = int(np.argmax(sims))
        return self.kb["faqs"][int(self.faq_owner[best])], float(sims[best])

    def classify(self, clean: str):
        probs = self.model.predict_proba([clean])[0]
        i = int(np.argmax(probs))
        return str(self.model.classes_[i]), float(probs[i])

    def reply(self, message: str, last_intent=None, pending_offer=None):
        self._maybe_reload()
        clean = preprocess(message)
        company = self.kb.get("company", {})
        phone = company.get("phone", "")
        phone_uae = company.get("phone_uae", "")
        email_kenya = company.get("email_kenya", "")
        email_uae = company.get("email_uae", "")

        # conversational memory: "yes" accepts the previous offer
        if clean in YES and pending_offer and pending_offer in self.kb["intents"]:
            return self._intent_reply(pending_offer, 1.0, "followup")

        faq, faq_score = self.faq_search(clean)
        faq_exact = self.cfg.get("faq_exact_threshold", 0.9)
        faq_min = self.cfg.get("faq_threshold", 0.6)

        def faq_reply():
            return {"response": faq["a"], "intent": faq.get("intent", "faq"), "confidence": round(faq_score, 3),
                    "source": "faq", "offer": None, "offer_prompt": None}

        # Layer 1a: near-exact FAQ match wins outright
        if faq and faq_score >= faq_exact:
            return faq_reply()

        # Layer 2: confident intent prediction (trained on many phrasings, so it
        # beats a merely similar FAQ that shares product words)
        intent, conf = self.classify(clean) if clean else ("", 0.0)
        if intent and conf >= self.cfg.get("intent_threshold", 0.45) and intent in self.kb["intents"]:
            return self._intent_reply(intent, conf, "classifier")

        # Layer 1b: moderately similar FAQ when the classifier is unsure
        if faq and faq_score >= faq_min:
            return faq_reply()

        return {
            "response": f"I'm sorry, I didn't fully understand your question. Could you rephrase it? Or contact us in Kenya on {phone} or in the UAE on {phone_uae}. Email {email_kenya} or {email_uae} for immediate assistance.",
            "intent": intent or "unknown", "confidence": round(conf, 3), "source": "fallback",
            "offer": None, "offer_prompt": None,
        }

    def _intent_reply(self, intent, conf, source):
        e = self.kb["intents"][intent]
        # Staff-facing "[ADD ...]" placeholders must never reach customers
        answer = re.sub(r"\s*\[ADD [^\]]*\]", "", e["answer"]).strip()
        if e.get("offer_prompt"):
            answer = f"{answer}\n\n{e['offer_prompt']}"
        return {"response": answer, "intent": intent, "confidence": round(conf, 3), "source": source,
                "offer": e.get("offer"), "offer_prompt": e.get("offer_prompt")}
