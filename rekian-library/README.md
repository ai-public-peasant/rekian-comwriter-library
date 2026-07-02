# Rekian Library

`rekian-library` stores document formats and reusable content separately, then composes them into `.hwpx` outputs.

## Structure

- `formats/`: institution or meeting-style assets
- `contents/`: reusable policy/report content assets
- `taxonomies/`: document-type routing rules and controlled vocabularies
- `table_profiles/`: reusable table patterns selected by document type and reasoning need
- `scripts/`: composition and utility scripts
- `outputs/`: generated `.hwpx` files and temporary build folders

## First Assets

- `formats/gwangyang-chief-meeting`: Gwangyang executive meeting brief
- `formats/gwangyang-field-trip-result-report`: field-trip and benchmarking result report
- `formats/gwangyang-transition-official-letter`: official letter style for Gwangyang transition committee documents
- `formats/mss-project-plan-2023`: MSS project-plan skeleton for Ministry of SMEs and Startups style documents
- `contents/local-ai-agent`: Local AI agent proposal
- `taxonomies/document_types.json`: baseline document-type taxonomy for format routing
- `table_profiles/regional-case-photo-summary`: photo-left, case-summary-right table profile for regional case review appendices

## How Composition Works

`scripts/compose_hwpx.py` builds a document in three steps:

1. Copy `formats/<format-id>/unpacked/` (an unzipped reference `.hwpx`) into a build folder.
2. Walk the non-empty text nodes of `Contents/section0.xml` in order and inject values from
   `contents/<content-id>/content.json`, following the `text_bindings` list in `format.json`.
3. Re-zip the build folder into `outputs/<format-id>__<content-id>.hwpx`.

**This repository does not ship any `unpacked/` folders.** An unpacked folder is the original
reference document itself, and the sanitization policy keeps original documents out of the
repository. The committed format assets are structure profiles only, so the composer cannot run
on the sample assets as-is. You run it against your own reference document.

## Run It With Your Own Reference

```bash
# 1. Unpack your own reference .hwpx into the format asset
python ../skills/hwpx-rekian/scripts/office/unpack.py my-reference.hwpx formats/my-format/unpacked

# 2. Generate the sanitized profile files (format_profile.json, placeholder_schema.json, README)
python scripts/extract_format_profile.py \
  --input my-reference.hwpx \
  --format-id my-format \
  --label "내 서식" \
  --description "내 레퍼런스 서식 프로필"

# 3. Author the bindings in formats/my-format/format.json
#    - use formats/gwangyang-chief-meeting/format.json as the schema example
#    - add "unpacked_dir", "paths", "metadata", "preview_bindings", "text_bindings"
#    - text_bindings must have exactly one entry per non-empty text node in section0.xml
#      (the count is in format_profile.json's non_empty_text_node_count; a mismatch raises an error)

# 4. Write your content asset
#    contents/my-content/content.json  (use contents/national-budget-db as the schema example)

# 5. Compose
python scripts/compose_hwpx.py --format my-format --content my-content
# -> outputs/my-format__my-content.hwpx
```

Keep `unpacked/` local: it contains your original document. It is intentionally not committed
here, and new format assets you publish should follow the same rule (profile files only).

The committed samples serve as schema references: `formats/gwangyang-chief-meeting/format.json`
shows a complete binding set, and `contents/*/content.json` show the content shape it maps from.

## Design Rule

- Format assets own layout, text-node order, and reference HWPX resources.
- Content assets own meaning and reusable message blocks.
- The composer maps content fields into format slots and emits a new `.hwpx`.
- New municipalities should usually add a new `formats/<format-id>` asset, not fork the content.
- Document type taxonomies route the task before a format is selected.
- Table profiles are reusable reasoning layouts; they should be selected by document type and evidence shape, not copied as placeholders.

## Sanitization Rule

- Do not commit original reference `.hwpx` files to this repository.
- Do not commit original preview images such as `Preview/PrvImage.png`.
- Format assets stored here must preserve structure and layout, but replace original body text with placeholders or neutral text.
- Content assets must not identify a specific municipality, writer, internal budget amount, or personal information.
- Public examples should describe reusable policy or workflow logic, not local-only facts.
- Table profiles should store structure, slot semantics, and generation constraints. Keep project-specific facts in provenance notes or separate content assets.
