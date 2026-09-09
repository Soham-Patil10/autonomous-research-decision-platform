"""Build the document corpus from data/sources.yaml.

    python scripts/fetch_corpus.py              # fetch everything automatable
    python scripts/fetch_corpus.py --only eu_afir_2023R1804
    python scripts/fetch_corpus.py --check      # report status, download nothing

Writes data/documents/MANIFEST.json recording, per document: source URL, SHA-256,
byte size, licence and fetch timestamp. That file is the provenance chain - the
ingester attaches it to chunk metadata so a citation in a report can be traced all
the way back to the URL it came from.

Nothing here fails silently. Every source reports OK / FAILED / MANUAL individually,
and a failure prints the URL so you can fix it in the manifest rather than in code.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_IN = ROOT / "data" / "sources.yaml"
DOCS_DIR = ROOT / "data" / "documents"
MANIFEST_OUT = DOCS_DIR / "MANIFEST.json"

TIMEOUT = 60
UA = "Mozilla/5.0 (compatible; arp-corpus-fetcher/0.1)"

# The SEC requires a real contact address in the User-Agent and rate-limits to
# ~10 req/s. Without this set, EDGAR sources are skipped rather than 403'd.
SEC_CONTACT = os.environ.get("CORPUS_CONTACT_EMAIL", "")


class FetchError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# HTTP
# --------------------------------------------------------------------------- #
def _get(url: str, *, accept: str = "*/*", user_agent: str = UA) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": accept, "Accept-Language": "en"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            body = response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(f"HTTP {exc.code} {exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise FetchError(f"unreachable: {exc.reason}") from exc
    except Exception as exc:  # noqa: BLE001
        raise FetchError(str(exc)) from exc

    if not body:
        raise FetchError("empty response body (proxy interstitial or bot block?)")
    return body


# --------------------------------------------------------------------------- #
# Source kinds
# --------------------------------------------------------------------------- #
def fetch_auto(source: dict[str, Any]) -> bytes:
    return _get(source["url"])


def fetch_edgar(source: dict[str, Any]) -> bytes:
    """Resolve a company's most recent filing of `form` via the SEC submissions API.

    data.sec.gov returns the filing index as parallel arrays; we walk them to find
    the newest matching form and then pull its primary document.
    """
    if not SEC_CONTACT:
        raise FetchError("set CORPUS_CONTACT_EMAIL=you@example.com (SEC requires a contact)")

    ua = f"arp-corpus-fetcher {SEC_CONTACT}"
    cik = source["cik"].lstrip("0")
    form_wanted = source.get("form", "10-K")

    index = json.loads(
        _get(
            f"https://data.sec.gov/submissions/CIK{source['cik']}.json",
            accept="application/json",
            user_agent=ua,
        )
    )
    recent = index.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accessions = recent.get("accessionNumber", [])
    documents = recent.get("primaryDocument", [])

    for form, accession, document in zip(forms, accessions, documents):
        if form != form_wanted:
            continue
        folder = accession.replace("-", "")
        return _get(
            f"https://www.sec.gov/Archives/edgar/data/{cik}/{folder}/{document}",
            user_agent=ua,
        )

    raise FetchError(f"no {form_wanted} found in recent filings for CIK {source['cik']}")


FETCHERS = {"auto": fetch_auto, "edgar": fetch_edgar}


# --------------------------------------------------------------------------- #
# Driver
# --------------------------------------------------------------------------- #
def load_sources() -> list[dict[str, Any]]:
    data = yaml.safe_load(MANIFEST_IN.read_text(encoding="utf-8"))
    return data.get("sources", [])


def load_existing_manifest() -> dict[str, Any]:
    if MANIFEST_OUT.exists():
        return json.loads(MANIFEST_OUT.read_text(encoding="utf-8"))
    return {}


def fetch_all(only: str | None = None, check_only: bool = False, force: bool = False) -> int:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_existing_manifest()
    sources = load_sources()

    ok = failed = skipped = manual = 0
    manual_todo: list[dict[str, Any]] = []

    for source in sources:
        sid = source["id"]
        if only and sid != only:
            continue

        target = DOCS_DIR / source["filename"]
        kind = source.get("kind", "auto")

        if kind == "manual":
            manual += 1
            if not target.exists():
                manual_todo.append(source)
            continue

        if check_only:
            state = "present" if target.exists() else "missing"
            print(f"  [check ] {sid:<32} {state}")
            continue

        if target.exists() and not force:
            print(f"  [skip  ] {sid:<32} already present ({target.stat().st_size:,} bytes)")
            skipped += 1
            continue

        try:
            body = FETCHERS[kind](source)
        except FetchError as exc:
            print(f"  [FAILED] {sid:<32} {exc}")
            print(f"           url: {source.get('url') or source.get('cik')}")
            failed += 1
            continue

        target.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        manifest[source["filename"]] = {
            "id": sid,
            "title": source["title"],
            "source_url": source.get("url", f"SEC EDGAR CIK {source.get('cik')}"),
            "license": source.get("license", ""),
            "redistributable": source.get("redistributable", False),
            "sha256": digest,
            "bytes": len(body),
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }
        print(f"  [ok    ] {sid:<32} {len(body):>10,} bytes  {digest[:12]}")
        ok += 1

    if not check_only:
        MANIFEST_OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    _report(ok, failed, skipped, manual, manual_todo, full_run=only is None)
    return 1 if failed else 0


def _report(
    ok: int,
    failed: int,
    skipped: int,
    manual: int,
    todo: list[dict[str, Any]],
    full_run: bool = True,
) -> None:
    print()
    print(f"fetched {ok}, skipped {skipped}, failed {failed}, manual {manual}")

    if todo:
        print("\nDownload these by hand into data/documents/ :\n")
        for source in todo:
            flag = "" if source.get("redistributable") else "  [DO NOT COMMIT]"
            print(f"  - {source['filename']}{flag}")
            print(f"      {source['title']}")
            print(f"      {source['url']}")
            if note := source.get("notes"):
                print(f"      note: {' '.join(note.split())}")
            print()

    if failed:
        print("Some sources failed. Fix the url in data/sources.yaml and re-run;")
        print("do not hardcode replacements in this script.")

    if full_run:
        print("Then write the four synthetic internal documents listed under")
        print("`synthetic_internal:` in data/sources.yaml - the private-corpus half of")
        print("hybrid RAG proves nothing without them.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", help="fetch a single source id")
    parser.add_argument("--check", action="store_true", help="report status, download nothing")
    parser.add_argument("--force", action="store_true", help="re-download files already present")
    args = parser.parse_args()

    print(f"corpus -> {DOCS_DIR}\n")
    return fetch_all(only=args.only, check_only=args.check, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
