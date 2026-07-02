---
name: rekian-library
description: Rekian format/content library guide. Use when you need to inspect reusable document formats and content assets before choosing a new HWPX reference.
---

# Rekian Library

`rekian-library` is the asset library behind `hwpx-rekian`.

Its job is not to generate a document by itself. Its job is to answer:

- what reusable formats already exist
- what reusable content assets already exist
- whether the requested document should reuse an existing format or require a new extraction

## Library Path

Primary path:

- `<repo-root>/rekian-library`

Key folders:

- `formats/`: sanitized format assets
- `contents/`: reusable content assets
- `scripts/`: composer and utility scripts
- `README.md`: design and sanitization rules

## Default Workflow

1. Inspect `formats/*/format.json` first.
2. Summarize available format ids, labels, and one-line descriptions.
3. If the user asked for redrafting, ask which existing format should be used.
4. If no existing format fits, say that a new format extraction is needed.
5. If content reuse is relevant, inspect `contents/*/content.json` and propose a reusable content asset.

## Response Rule

When the library contains plausible choices, do not jump straight into raw reference analysis.

Instead ask a short format-selection question such as:

- `현재 라이브러리에 gwangyang-chief-meeting, mss-project-plan-2023 포맷이 있습니다. 어느 서식으로 갈까요?`

If the library clearly has no suitable format, say so directly and move on to new reference extraction.

## Sanitization Rule

Treat this library as a public-safe asset store.

- Do not rely on original `reference.hwpx` files being present.
- Do not rely on original `Preview/PrvImage.png` files being present.
- Assume formats are sanitized structure assets.
- Assume content assets should avoid municipality-specific details, writer identity, internal budgets, and personal information.

## Typical Use Cases

- `rekian에서 쓸 수 있는 서식 뭐 있어?`
- `이 안건을 기존 라이브러리 서식으로 만들 수 있어?`
- `새 레퍼런스 따기 전에 이미 있는 format부터 보여줘`
- `다른 세션에서도 rekian format 목록부터 확인하게 해줘`
