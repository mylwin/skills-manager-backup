---
name: literature-pdf-translate
description: Translate academic literature and PDF documents locally with the user's configured translation service. Use this skill whenever the user asks to translate a paper, article, research document, or PDF, including requests for a bilingual dual-column PDF, a translation-only PDF, or a PDF attached in chat. Guide the user through file selection and output type, then require explicit confirmation before starting the local server or submitting any translation job.
---

# Local PDF Translation

Use the existing local project at `/Users/myl/Documents/zotero-pdf2zh`.

## Workflow

1. Check whether the user supplied a local PDF path or an attachment. If neither is available, ask only for the PDF path.
2. Determine the output type. If the user has not said which one they want, ask them to choose:
   - `dual`: bilingual dual-column PDF, with original and translation side by side.
   - `mono`: translation-only PDF.
3. Reuse the current conversation's translation service choice when one exists. Otherwise use `pdf2zh_next` with the project's configured default service, `siliconflowfree`. If the user names a provider such as `deepseek`, `openai`, `ollama`, or `siliconflow`, pass that provider as `next_service` and let the project read its existing configuration from `server/config/config.toml`.
4. Before executing anything that starts the server or submits a translation, show a concise confirmation summary containing:
   - input PDF path
   - source and target languages (default `en` to `zh-CN`)
   - output type
   - translation engine and service
   - exact commands or endpoint action that will be executed
   Ask for explicit confirmation. Do not infer approval from the original translation request.
5. Before asking for confirmation, a read-only health check of `http://127.0.0.1:8890/health` is allowed. If the service is healthy, do not start another server.
6. After confirmation, start the server only when needed:

   ```bash
   cd /Users/myl/Documents/zotero-pdf2zh/server
   cp config/config.toml .runtime-config.toml.bak
   mkdir -p .runtime-home
   HOME="$PWD/.runtime-home" nohup /opt/homebrew/Caskroom/miniconda/base/envs/zotero-pdf2zh-server/bin/python server.py --env_tool=conda --check_update=False > standalone-server.log 2>&1 & echo $! > standalone-server.pid
   ```

   The server currently refreshes live config files from their `.example` files during startup. Once `/health` returns successfully, restore the saved `config.toml` before submitting the translation:

   ```bash
   cp .runtime-config.toml.bak config/config.toml
   ```

   If startup fails, restore the backup before reporting the failure. Record whether the service was already healthy. Only a server started by this workflow may be stopped later.
7. After confirmation, submit the PDF with `scripts/translate_pdf.py`. Run it with the `zotero-pdf2zh-server` Conda environment and pass the selected input path and output type.
8. Report the generated files under `/Users/myl/Documents/zotero-pdf2zh/server/translated/` and provide absolute paths. Do not claim success until the API reports success and the files exist.
9. After reporting a completed or failed job, ask whether to close the current translation service. If the user confirms and this workflow started the service, first verify that the recorded PID still belongs to this project's `server.py`, then send it `TERM`, verify that `/health` is no longer responding, and remove the PID file and temporary config backup. If the service was already running before this workflow, explain that it was left running and do not stop it.

## Translation parameters

Use `pdf2zh_next` by default. For output selection, the server requires both the positive and negative flags:

- `dual`: send `dual=true`, `mono=false`, `noMono=true`, `noDual=false`.
- `mono`: send `mono=true`, `dual=false`, `noMono=false`, `noDual=true`.

Keep `noWatermark=true` unless the user requests a watermark. Use `sourceLang=en` and `targetLang=zh-CN` unless the user specifies other language codes. For scanned PDFs, ask whether OCR should be enabled only if the user has not already specified it and the file appears to require OCR.

The helper sends an empty `llm_api` object by default so existing provider settings in `server/config/config.toml` remain authoritative. Never print or repeat API keys in chat or logs. Do not edit the project's configuration merely to perform a one-off translation.

## Error handling

- If `/health` is unavailable after startup, read `server/standalone-server.log`, summarize the relevant error, and stop instead of submitting the PDF.
- Always restore `.runtime-config.toml.bak` to `config/config.toml` if startup or translation setup fails after the server has refreshed the example configuration.
- If translation fails, report the API error and the log path. Do not retry automatically because a retry can duplicate API usage.
- If the input is not a PDF or cannot be read, ask for a valid local PDF path.
- Do not start or submit a job without explicit confirmation in the current turn.
- Never stop an untracked or pre-existing server process merely because a translation finished.

## Helper

Read the helper's `--help` output when needed. It is intentionally a small standard-library client so it can submit a PDF without a reference manager or additional packages.
