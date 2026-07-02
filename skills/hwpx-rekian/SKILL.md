---
name: hwpx-rekian
description: 공문서·보고서 재기안 특화 HWPX 스킬. 기존 지자체나 기관 문서를 레퍼런스로 삼아 서식, 블록 구성, 결재선, 표, 문체를 최대한 비슷하게 새 문서로 옮기고, 반복 사용 서식은 Rekian library의 format_profile로 캐시해야 할 때 사용한다. 일반적인 HWPX 읽기/생성/수정은 `hwpx`를 사용한다.
---

# HWPX Rekian

`hwpx-rekian` is the reference-driven redrafting skill.

이 스킬의 목적은 HWPX를 "다룬다"가 아니라, 기존 공문서를 "재기안"하는 것이다.

Use this skill when the user means:

- `재기안`
- `서식 복제`
- `유사 보고서 작성`
- `다른 지자체 버전 만들기`
- `기존 문서 스타일을 최대한 따라가기`
- `레퍼런스 문서와 거의 같은 흐름으로 새 문서 작성`

Do not use this skill for generic `.hwpx` inspection or one-off document generation without a reference.  
그 경우는 `hwpx`가 맞다.

## Core Principle

핵심은 "새 문서를 예쁘게 만든다"가 아니라 "레퍼런스 문서의 형식 논리를 보존한다"이다.

우선 보존해야 하는 것:

- 상단 결재부와 기관문서 흐름
- 제목, 요약, 본문 블록 순서
- 문단 밀도와 표 배치 리듬
- 레퍼런스의 공공문서 톤
- 페이지 구성과 형식적 인상

바꿔야 하는 것:

- 기관명
- 담당 부서/직위/연락처
- 지역명, 사업명, 예산 수치, 일정 등 사실값
- 해당 기관에 맞지 않는 고유 정보

## Primary Resources

이 스킬은 내부적으로 `hwpx` 계열 도구를 재사용할 수 있다.  
하지만 판단 기준은 항상 "형식 재현"이다.

- `scripts/analyze_template.py`: 레퍼런스 문서 구조 분석
- `scripts/text_extract.py`: 원문 내용 추출
- `scripts/office/unpack.py`: XML 단위로 레이아웃 확인
- `scripts/build_hwpx.py`: 재구성한 header/section으로 새 파일 조립
- `templates/`: 기본 골격 출발점
- `examples/`: 샘플 흐름 참고

## COM Backend

`hwpx-rekian` decides what must be preserved. It should not duplicate the detailed Hancom COM rules.

When a redrafting task needs HWP legacy conversion, Hancom-rendered fidelity, COM-only insertion/replacement, SaveAs-based HWPX generation, or XML postprocessing after COM output, use `hwp-com-writer` as the execution backend.

Use `hwp-com-writer` when:

- the input is `.hwp` and must be converted to `.hwpx`
- visual fidelity depends on Hancom's own rendering engine
- XML-only editing risks breaking tables, fixed layout, or nested document structure
- the work requires COM SaveAs, security module registration, table insertion, cell styling, or hybrid XML postprocessing

Keep the division of responsibility clear:

- `hwpx-rekian`: reference analysis, preservation decisions, public-document tone, and redrafting flow
- `hwp-com-writer`: Hancom COM automation, HWP/HWPX conversion, precise rendering operations, and postprocess patches

## Rekian Library First

Before asking the user for a brand-new reference, check whether `rekian-library` already has a reusable format.

Primary library path:

- `<repo-root>/rekian-library`

What to inspect first:

- `formats/*/format.json`: reusable format assets
- `formats/*/format_profile.json`: cached structure, slot, and layout profile
- `formats/*/placeholder_schema.json`: semantic input contract for generation
- `contents/*/content.json`: reusable content assets
- `README.md`: library rules, especially sanitization and composition expectations

Default behavior:

1. Inspect the library formats and cached profiles first.
2. If one or more formats look relevant, briefly list them for the user.
3. If a matching `format_profile.json` exists, use it before re-reading the raw reference.
4. Ask which format the user wants to use before requesting a new raw reference document.
5. Only fall back to extracting a new format when the library does not contain a suitable candidate.

When listing library choices, prefer format id + one-line description, for example:

- `gwangyang-chief-meeting`: one-page executive meeting brief
- `mss-project-plan-2023`: Ministry of SMEs and Startups project plan skeleton

## Format Profile Cache

For slow or repeatable document-generation work, separate reading from writing:

- Rekian reads the reference once and stores the read structure in `rekian-library`.
- COM-writer loads that profile and generates the actual HWPX/PDF.

Profile files live under `formats/<format-id>/`:

- `format.json`: asset id, label, description, and workflow metadata
- `format_profile.json`: package type, section/table/cell counts, text-node count, resource count, slot detection, zone map, fingerprint, and source audit
- `placeholder_schema.json`: semantic keys that COM-writer should fill

Use `rekian-library/scripts/extract_format_profile.py` to create or refresh the cache from a `.hwpx` or `.odt` reference. The profile must not copy the original document; store only structure, slots, hashes, and source audit metadata unless a sanitized template is intentionally created.

When handing off to `hwp-com-writer`, pass the format id and require this load order:

1. `formats/<format-id>/format.json`
2. `formats/<format-id>/format_profile.json`
3. `formats/<format-id>/placeholder_schema.json`

Only refresh the raw reference when the cached profile lacks a required slot, the source format changed, or visual verification fails.

## Required Inputs

가능하면 아래를 먼저 확보한다.

- library에서 바로 쓸 수 있는 format 후보
- 레퍼런스 문서 1개 이상
- 목표 기관명과 부서명
- 바뀌는 사실값 목록
- 유지해야 할 페이지 수나 보고 형식 제약

레퍼런스가 없으면 `hwpx-rekian`의 강점이 줄어든다.  
그 경우는 먼저 템플릿 후보를 정하거나 `hwpx` 방식의 범용 생성으로 전환할지 판단한다.

## Recommended Workflow

1. 레퍼런스 문서의 제목 체계, 결재부, 본문 블록, 표 패턴을 먼저 분석한다.
2. 그대로 유지할 형식 요소와 바꿔야 할 기관별 요소를 분리한다.
3. 레퍼런스의 문서 흐름을 기준으로 새 내용 초안을 맞춘다.
4. 필요하면 `header.xml`, `section0.xml`, 표 구조를 추출하거나 재조합한다.
5. 최종 결과가 "새 문서"이면서도 "같은 부류의 문서"로 보이는지 확인한다.

## Behavioral Rule

- 사용자가 레퍼런스를 줬다면 새로운 스타일을 임의로 제안하지 않는다.
- 시각적 100% 복제가 어렵더라도, 블록 순서와 형식 인상은 최대한 유지한다.
- 내용 치환 때문에 문서 톤이 무너지지 않게 공공문서 문체를 정돈한다.
- 필요한 경우 레퍼런스와 달라진 부분을 명시적으로 기록한다.

## XML Guardrails

When redrafting XML directly, follow these rules by default:

- Replace only leaf paragraphs. Skip container paragraphs that contain nested `hp:tbl` or nested `hp:p`.
- Preserve the original bullet/number prefix run when the paragraph begins with `-`, `*`, `**`, `***`, `○`, `□`, numbered markers, or similar list prefixes.
- Remove every `hp:linesegarray` after text replacement so Hancom recalculates line breaks and spacing on open.
- Treat cover pages, TOCs, and nested-table blocks as format-specific zones. Do not blindly replace their outer wrapper paragraphs.

Use `scripts/rekian_xml.py` for these safeguards instead of rewriting the logic ad hoc.

## Common Prompt Shapes

이 스킬이 특히 잘 맞는 요청:

- "이 보고서 다른 지자체 버전으로 다시 써줘"
- "서식은 거의 그대로 두고 기관명만 바꿔줘"
- "이 공문 형식 따라 새 문서 만들어줘"
- "기존 보고전 스타일 베껴서 새 안건 넣어줘"
