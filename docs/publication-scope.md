# Publication Scope

This repository is a clean public packaging of Rekian, COM-writer, and the Rekian library pattern.

## Included

- Agent skill instructions for `hwpx-rekian`, `hwp-com-writer`, and `rekian-library`
- Pure-Python HWPX helper scripts and examples
- Hancom COM helper scripts and XML postprocess utilities
- Sanitized format profile examples
- Sanitized content and table-profile examples
- Document-type routing taxonomy
- Architecture notes explaining the collaboration model

## Excluded

- Original `.hwp` and `.hwpx` reference documents
- Generated `.hwpx` outputs
- Rendered PDFs and preview images
- Local Windows project paths
- Personal names, private phone numbers, internal-only notes, and local provenance paths
- Python bytecode and generated cache directories
- Prior local Git history from staging folders

## Sanitization Policy

Format profiles may preserve structural counts, slot labels, zone maps, and layout constraints. They must not publish raw reference documents or reproduce private body text.

Content examples should be reusable and non-personal. If a content asset is based on real administrative work, keep only the reusable policy/report logic and remove local-only facts.
