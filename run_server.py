"""Entry point used both in development and inside the PyInstaller executable."""
import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

import uvicorn

BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
os.chdir(BASE_DIR)
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

(BASE_DIR / "logs").mkdir(exist_ok=True)
handler = RotatingFileHandler(BASE_DIR / "logs" / "server.log", maxBytes=2_000_000, backupCount=5, encoding="utf-8")
logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()],
                    format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from app.main import app  # noqa: E402  (imported directly so PyInstaller bundles it)

if __name__ == "__main__":
    cfg = json.loads((BASE_DIR / "config.json").read_text(encoding="utf-8"))
    # log_config=None: the default uvicorn logging config breaks in windowed/frozen builds
    uvicorn.run(app, host=cfg.get("host", "127.0.0.1"), port=int(cfg.get("port", 8000)), log_config=None)
