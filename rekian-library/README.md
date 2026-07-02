# Rekian Library

`rekian-library`는 문서 서식(format)과 재사용 콘텐츠(content)를 분리해서 저장하고, 둘을 조합해 `.hwpx` 산출물을 만드는 자산 라이브러리입니다.

## 구조

- `formats/`: 기관·회의 스타일별 서식 자산
- `contents/`: 재사용 가능한 정책/보고 콘텐츠 자산
- `taxonomies/`: 문서 유형 라우팅 규칙과 통제 어휘
- `table_profiles/`: 문서 유형과 논리 구조에 따라 선택하는 재사용 표 패턴
- `scripts/`: 조립·유틸리티 스크립트
- `outputs/`: 생성된 `.hwpx`와 임시 빌드 폴더

## 기본 자산

- `formats/gwangyang-chief-meeting`: 광양시 직속실회의 1페이지 보고 서식
- `formats/gwangyang-field-trip-result-report`: 선진지 견학·벤치마킹 결과보고서 서식
- `formats/gwangyang-transition-official-letter`: 인수위원회형 공문 서식
- `formats/mss-project-plan-2023`: 중소벤처기업부 스타일 사업계획서 골격
- `contents/local-ai-agent`: 로컬 AI 에이전트 도입 검토 콘텐츠 예시
- `taxonomies/document_types.json`: 서식 라우팅용 기본 문서유형 분류
- `table_profiles/regional-case-photo-summary`: 좌측 사진 + 우측 사례요약 배치의 붙임형 사례검토 표 프로필

## 조립 동작 원리

`scripts/compose_hwpx.py`는 세 단계로 문서를 만듭니다.

1. `formats/<format-id>/unpacked/`(레퍼런스 `.hwpx`를 압축 해제한 폴더)를 빌드 폴더로 복사합니다.
2. `Contents/section0.xml`의 비어 있지 않은 텍스트 노드를 순서대로 돌면서, `format.json`의 `text_bindings` 목록에 따라 `contents/<content-id>/content.json` 값을 주입합니다.
3. 빌드 폴더를 다시 압축해 `outputs/<format-id>__<content-id>.hwpx`로 내보냅니다.

**이 저장소에는 `unpacked/` 폴더가 포함되어 있지 않습니다.** unpacked 폴더는 원본 레퍼런스 문서 그 자체이고, 공개 정책상 원본 문서는 저장소에 올리지 않기 때문입니다. 커밋된 서식 자산은 구조 프로필뿐이므로 샘플 자산만으로는 컴포저를 바로 실행할 수 없고, 자신의 레퍼런스 문서를 가지고 실행해야 합니다.

## 자기 레퍼런스로 실행하기

```bash
# 1. 자신의 레퍼런스 .hwpx를 서식 자산 안에 압축 해제
python ../skills/hwpx-rekian/scripts/office/unpack.py my-reference.hwpx formats/my-format/unpacked

# 2. 정제된 프로필 파일 생성 (format_profile.json, placeholder_schema.json, README)
python scripts/extract_format_profile.py \
  --input my-reference.hwpx \
  --format-id my-format \
  --label "내 서식" \
  --description "내 레퍼런스 서식 프로필"

# 3. formats/my-format/format.json에 바인딩 작성
#    - 스키마 예시는 formats/gwangyang-chief-meeting/format.json 참조
#    - "unpacked_dir", "paths", "metadata", "preview_bindings", "text_bindings" 추가
#    - text_bindings는 section0.xml의 비어 있지 않은 텍스트 노드 개수와 정확히 1:1이어야 함
#      (개수는 format_profile.json의 non_empty_text_node_count에 있으며, 불일치 시 에러 발생)

# 4. 콘텐츠 자산 작성
#    contents/my-content/content.json  (스키마 예시는 contents/national-budget-db 참조)

# 5. 조립
python scripts/compose_hwpx.py --format my-format --content my-content
# -> outputs/my-format__my-content.hwpx
```

`unpacked/`는 로컬에만 둡니다. 원본 문서가 들어 있으므로 의도적으로 커밋하지 않으며(.gitignore 처리됨), 새 서식 자산을 공개할 때도 같은 규칙(프로필 파일만 공개)을 따릅니다.

커밋된 샘플의 역할은 스키마 참고용입니다. `formats/gwangyang-chief-meeting/format.json`은 완성된 바인딩 세트의 예시이고, `contents/*/content.json`은 바인딩이 매핑해 가는 콘텐츠 형태의 예시입니다.

## 설계 규칙

- 서식 자산은 레이아웃, 텍스트 노드 순서, 레퍼런스 HWPX 리소스를 책임진다.
- 콘텐츠 자산은 의미와 재사용 가능한 메시지 블록을 책임진다.
- 컴포저는 콘텐츠 필드를 서식 슬롯에 매핑해 새 `.hwpx`를 만든다.
- 새 지자체 대응은 보통 콘텐츠를 복제하는 게 아니라 새 `formats/<format-id>` 자산을 추가하는 방식으로 한다.
- 문서유형 분류(taxonomy)가 서식 선택 이전의 라우팅을 담당한다.
- 표 프로필은 재사용 가능한 논리 레이아웃이며, 문서 유형과 근거자료 형태에 따라 선택한다. placeholder처럼 복사해 쓰는 용도가 아니다.

## 정제(공개 안전) 규칙

- 원본 레퍼런스 `.hwpx` 파일을 이 저장소에 커밋하지 않는다.
- `Preview/PrvImage.png` 같은 원본 미리보기 이미지를 커밋하지 않는다.
- 여기 저장하는 서식 자산은 구조와 레이아웃은 보존하되, 원본 본문 텍스트는 placeholder나 중립 텍스트로 교체해야 한다.
- 콘텐츠 자산에는 특정 지자체 식별 정보, 작성자, 내부 예산액, 개인정보를 넣지 않는다.
- 공개 예시는 로컬 전용 사실이 아니라 재사용 가능한 정책·업무 논리를 담아야 한다.
- 표 프로필에는 구조, 슬롯 의미, 생성 제약만 저장한다. 프로젝트 고유 사실은 provenance 메모나 별도 콘텐츠 자산으로 분리한다.
