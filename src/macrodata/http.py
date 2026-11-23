"""Camada HTTP com cache em disco, retries e manifesto de proveniência."""
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from . import settings

MANIFEST_PATH = settings.PROCESSED / "manifest.json"
_UA = {"User-Agent": "curl/8.18.0"}


def _load_manifest() -> dict[str, Any]:
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    return {"created_at": settings.EXTRACTION_TS, "entries": {}}


def _save_manifest(man: dict[str, Any]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as fh:
        json.dump(man, fh, ensure_ascii=False, indent=2, sort_keys=True)


class CachedFetcher:
    """Baixa e cacheia recursos. O cache é reutilizado entre execuções.

    A chave do manifesto é a URL; guardamos timestamp, status, tamanho, sha256,
    caminho local e um `vintage` (data de extração) para auditoria.
    """

    def __init__(self, force: bool = False, pause: float = 0.15, timeout: int = 90):
        self.force = force
        self.pause = pause
        self.timeout = timeout
        self.manifest = _load_manifest()
        self.session = requests.Session()
        self.session.headers.update(_UA)

    def _record(self, url: str, path: Path, status: int, payload: bytes) -> None:
        self.manifest["entries"][url] = {
            "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "status": status,
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "path": str(path.relative_to(settings.ROOT)),
        }
        _save_manifest(self.manifest)

    def fetch(self, url: str, relpath: str, *, force: bool | None = None,
              validate=None) -> bytes:
        force = self.force if force is None else force
        path = settings.RAW / relpath
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not force and path.stat().st_size > 0:
            return path.read_bytes()
        last_err: Exception | None = None
        for attempt in range(5):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code in (400, 401, 403, 404, 410):
                    raise FileNotFoundError(f"HTTP {resp.status_code}: {url}")
                payload = resp.content
                if validate is not None:
                    validate(payload)
                path.write_bytes(payload)
                self._record(url, path, resp.status_code, payload)
                time.sleep(self.pause)
                return payload
            except FileNotFoundError as exc:
                raise RuntimeError(str(exc)) from exc
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Falha ao baixar {url}: {last_err}") from last_err

    def get_json(self, url: str, relpath: str, **kw) -> Any:
        return json.loads(self.fetch(url, relpath, **kw).decode("utf-8"))

    def get_text(self, url: str, relpath: str, **kw) -> str:
        return self.fetch(url, relpath, **kw).decode("utf-8", errors="replace")

    def get_csv(self, url: str, relpath: str, **kw) -> pd.DataFrame:
        from io import BytesIO
        return pd.read_csv(BytesIO(self.fetch(url, relpath, **kw)))


def to_num(series: pd.Series) -> pd.Series:
    """Converte strings numéricas com vírgula/ponto e marcadores de missing."""
    s = series.astype(str).str.strip()
    s = s.replace({".": None, "..": None, "": None, "NA": None, "n/a": None, "nan": None})
    s = s.str.replace("\u00a0", "", regex=False).str.replace(" ", "", regex=False)
    # formatos 1.234,56 (europeu) vs 1234.56
    mask = s.str.contains(r",\d", regex=True, na=False) & s.str.contains(r"\.", regex=True, na=False)
    s = s.where(~mask, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False))
    s = s.str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def q_from_date(dates: pd.Series) -> pd.Series:
    d = pd.to_datetime(dates)
    return d.dt.year.astype(str) + "Q" + d.dt.quarter.astype(str)


def quarter_end(year: int, q: int) -> pd.Timestamp:
    return pd.Timestamp(year=year, month=3 * q, day=1) + pd.offsets.MonthEnd(0)
