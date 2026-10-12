#!/usr/bin/env python3
"""Submit one local PDF to the zotero-pdf2zh server and print output paths."""

import argparse
import base64
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-type", choices=("dual", "mono"), required=True)
    parser.add_argument("--service", default="siliconflowfree")
    parser.add_argument("--source", default="en")
    parser.add_argument("--target", default="zh-CN")
    parser.add_argument("--server", default="http://127.0.0.1:8890")
    args = parser.parse_args()

    pdf = args.input.expanduser().resolve()
    if not pdf.is_file() or pdf.suffix.lower() != ".pdf":
        print(f"Input must be an existing PDF: {pdf}", file=sys.stderr)
        return 2

    dual = args.output_type == "dual"
    payload = {
        "fileName": pdf.name,
        "fileContent": "data:application/pdf;base64,"
        + base64.b64encode(pdf.read_bytes()).decode("ascii"),
        "engine": "pdf2zh_next",
        "next_service": args.service,
        "sourceLang": args.source,
        "targetLang": args.target,
        "mono": not dual,
        "dual": dual,
        "noMono": dual,
        "noDual": not dual,
        "noWatermark": True,
        "llm_api": {},
    }
    request = urllib.request.Request(
        args.server.rstrip("/") + "/translate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=86400) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(f"Translation request failed ({exc.code}): {detail}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Translation request failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") != "success":
        return 1

    for name in result.get("fileList", []):
        print(args.server.rstrip("/") + "/translatedFile/" + urllib.parse.quote(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
