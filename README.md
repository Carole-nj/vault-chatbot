# Vault Electronics Chatbot

FastAPI + scikit-learn (TF-IDF + Linear SVM) chatbot with an embeddable website widget, built from the project proposal.

## Layout

```
app/            FastAPI backend (main.py), NLP + layered logic (nlp.py), SQLite (db.py)
data/           knowledge_base.json (staff-editable), training_data.csv (generated)
scripts/        generate_training_data.py, train_model.py, check_knowledge_base.py
models/         intent_model.joblib (created by training)
reports/        metrics.json, confusion_matrix.csv (created by training)
widget/         vault-chatbot.js (the embeddable widget), index.html (demo page)
installer/      build_windows.bat, vault_chatbot.iss (Inno Setup), start_ngrok.bat, backup_data.bat
tests/          pytest API tests
run_server.py   entry point (dev and packaged exe)
config.json     port, allowed origins, thresholds, admin token
```

## Run locally

```
pip install -r requirements.txt
python scripts/generate_training_data.py
python scripts/train_model.py
python run_server.py
```

Open http://127.0.0.1:8000/widget/ and click the chat bubble. Run the tests with `pytest tests`.

## How a message is answered

1. A near-exact FAQ match is answered directly.
2. Otherwise the intent classifier answers if its confidence is at least `intent_threshold` (0.45).
3. Otherwise a moderately similar FAQ (at least `faq_threshold`, 0.6) is used.
4. Otherwise the fallback message with the phone number is returned, and the question is logged (`/stats` lists recent unanswered ones).

Replying "yes" after an offer ("Would you like a quote?") follows the offer. The bot never learns automatically: review `/stats`, add verified answers to the knowledge base and real questions to `data/seed_extra.csv` (columns `text,intent`), then rerun the two scripts.

## Before go-live (important)

- Run `python scripts/check_knowledge_base.py`. It lists answers still marked draft or containing `[ADD ...]`. **No prices, delivery times, opening hours, warranty periods or specs were invented**; Vault must supply them. Customers never see the `[ADD ...]` markers, but the answers stay generic until filled in.
- Change `admin_token` in `config.json` (it protects `/stats`; send it as the `X-Admin-Token` header).
- The shipped model scores about 100% only because the training data is generated from templates. Real accuracy will be lower. Collect real enquiries (WhatsApp, email, phone notes) into `data/seed_extra.csv`, retrain, and re-measure on held-out real messages.

## Website embed

```html
<script src="https://api.vaultelectronics.co.ke/widget/vault-chatbot.js"
        data-api="https://api.vaultelectronics.co.ke" defer></script>
```

Optional: `data-color="#0b3d5c"`, `data-title="Vault Assistant"`. Make sure the site's origin is in `allowed_origins` in `config.json`.

## Build the Windows installer

The `.exe` must be built on Windows (PyInstaller cannot cross-compile). On a Windows 10/11 machine with Python 3.10+ and Inno Setup 6, run:

```
installer\build_windows.bat
```

Output: `installer\Output\VaultChatbotSetup.exe`. It installs to Program Files, keeps `data\` and `config.json` across upgrades, registers start-at-boot tasks for the server and the ngrok tunnel (optional task), and uninstalls cleanly from Control Panel. Silent install:

```
VaultChatbotSetup.exe /VERYSILENT /SUPPRESSMSGBOXES /TASKS="autostart"
```

Note: PyInstaller bundles Python inside the exe, so the installer does not need a separate Python or virtual environment (this replaces proposal steps 2-3, and is more reliable).

## ngrok

Install ngrok on the production PC, run `ngrok config add-authtoken <TOKEN>` once, and set the reserved domain in `config.json` / `start_ngrok.bat`. Using your own domain (`api.vaultelectronics.co.ke`) requires a paid ngrok plan and a DNS CNAME. Keep the PC on 24/7 and schedule `installer\backup_data.bat` daily.

## Optional semantic search

`pip install sentence-transformers`, set `"use_embeddings": true` in `config.json`. This adds the BAAI/bge-small-en-v1.5 model to the FAQ search (a large download, so it is off by default and kept out of the installer).
