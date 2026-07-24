---
name: prozorro-cli
description: Use the installed prozorro-cli command only when the current user explicitly asks to retrieve or download a specific Prozorro tender JSON or its documents and provides, or has already provided, a concrete tender reference. Trigger for direct requests such as "download tender UA-...", "скачай тендер", "download the tender documents", or "скачай документы тендера". Do not use for general Prozorro questions, procurement analysis, tender discovery or search, coding and debugging, or requests without an explicit retrieval or download action.
---

# Prozorro CLI

Use the local `prozorro-cli` command to retrieve public data from the official
Prozorro API.

## Enforce the activation boundary

- Proceed only for an explicit request to retrieve or download one concrete
  tender or its documents.
- Accept a reference supplied earlier in the conversation when the current
  request clearly refers to that tender.
- Do not run the command merely because Prozorro, procurement, or tenders are
  being discussed.
- Do not search for tenders. Ask for a UA-ID, GUID, UUID, Prozorro tender URL,
  or Public API URL if no concrete reference is available.

## Check availability

After the activation boundary is satisfied, run:

```text
prozorro-cli --help
```

If the command is unavailable, tell the user to run
`pip install prozorro-cli`. Do not install software unless the user explicitly
asks for installation.

## Retrieve tender JSON

Run:

```text
prozorro-cli tender "<reference>"
```

For a download request, capture stdout, verify that it is valid JSON, and save
it as UTF-8. Honor a destination supplied by the user. Otherwise, choose a
collision-free `.json` path under `./prozorro-downloads/`. Never overwrite an
existing file.

For a request to display or inspect the tender rather than download it, parse
the JSON and return only the requested information unless the user explicitly
asks for the full payload.

## Download tender documents

Run:

```text
prozorro-cli documents "<reference>" --output "<directory>"
```

Honor an output directory supplied by the user. Otherwise, use a safe,
collision-free directory under `./prozorro-downloads/`. The command preserves
existing files by adding numeric suffixes to duplicate names.

Report the resulting directory and the downloaded file paths. Do not open any
downloaded document unless the user also asks to inspect it.

## Handle failures

- Preserve the CLI error message and explain the next actionable step.
- Do not retry invalid references with guessed identifiers.
- Do not replace the official endpoints used by `prozorro-cli` with unofficial
  procurement services.
- Do not use `--open` unless the user explicitly asks to open a tender page or
  API link in a browser.
