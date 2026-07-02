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

## Compose

```bash
python scripts/compose_hwpx.py --format gwangyang-chief-meeting --content local-ai-agent
```

Default output:

```text
outputs/gwangyang-chief-meeting__local-ai-agent.hwpx
```

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
