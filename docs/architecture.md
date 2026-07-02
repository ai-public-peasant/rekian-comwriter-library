# Architecture

Rekian separates document automation into three responsibilities.

## 1. `hwpx-rekian`

`hwpx-rekian` is the reader and redrafting planner.

It decides what must be preserved from a reference document:

- document type and reporting genre
- title, approval, body, appendix, table, and image zones
- paragraph density and public-document tone
- semantic slots that should be replaced by new content

It should prefer the cached `rekian-library` profile before re-reading a raw reference.

## 2. `rekian-library`

`rekian-library` is the public-safe asset store.

It stores:

- `formats/*/format.json`: reusable format metadata
- `formats/*/format_profile.json`: cached structural profile
- `formats/*/placeholder_schema.json`: semantic input contract
- `contents/*/content.json`: reusable content examples
- `table_profiles/*/table_profile.json`: reusable table patterns
- `taxonomies/document_types.json`: document-type routing rules

The library does not store original reference documents.

## 3. `hwp-com-writer`

`hwp-com-writer` is the execution backend.

It consumes a Rekian profile and then uses:

- Hancom COM for native layout operations, SaveAs, table insertion, and style application
- HWPX XML postprocess for things COM handles poorly, such as cell background, table flags, indentation units, and Korean official-document paragraph cleanup

## Handoff Flow

```text
User request
  ↓
rekian-library format/content lookup
  ↓
hwpx-rekian reference/profile decision
  ↓
format_profile.json + placeholder_schema.json
  ↓
hwp-com-writer COM execution
  ↓
HWPX XML postprocess
  ↓
render/open verification in Hancom
```

## Operating Rule

Use the smallest reliable surface:

- If a cached profile is enough, use it.
- If XML replacement is structurally safe, keep the workflow pure Python.
- If visual fidelity depends on Hancom's renderer, hand the job to COM-writer.
- If the raw reference is needed, extract a sanitized profile and keep the raw file out of the library.
