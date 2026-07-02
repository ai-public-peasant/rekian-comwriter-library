# Rekian COM Writer Library

Rekian은 HWPX 기반 공문서 재기안 툴킷입니다.

이 저장소는 함께 동작하도록 설계된 세 부분을 묶어 배포합니다.

- `skills/hwpx-rekian`: 레퍼런스 기반 HWPX 재기안 규칙과 XML 유틸리티
- `skills/hwp-com-writer`: 한컴 COM + HWPX XML 후처리 방식의 정밀 생성 백엔드
- `skills/rekian-library`: 재사용 가능한 서식·콘텐츠 자산을 고르는 스킬 가이드
- `rekian-library`: 개인정보를 제거한 서식 프로필, 콘텐츠 예시, 표 프로필, 문서유형 분류, 조립 스크립트

핵심 아이디어는 단순합니다. Rekian이 레퍼런스 문서를 한 번 읽고 분류해서 정제된 구조 프로필을 라이브러리에 저장하면, 한컴 렌더링 수준의 정밀 출력이 필요할 때 COM-writer가 그 프로필을 실행 계획으로 사용합니다.

역할 분담은 명확합니다. **Rekian은 읽는 쪽, COM-writer는 쓰는 쪽입니다.** `hwpx-rekian`은 레퍼런스를 분석하고 무엇을 보존할지 판단해 구조를 캐시하는 역할이며, 순수 XML 쓰기 능력은 제한적입니다. 실제 문서 생성은 기본적으로 `hwp-com-writer`가 담당합니다.

## 자기 레퍼런스 문서로 사용하기

이 저장소에는 **원본 레퍼런스 문서가 포함되어 있지 않습니다.** 커밋된 것은 정제된 구조 프로필뿐이므로, 샘플 자산만으로는 `.hwpx`를 바로 조립할 수 없습니다. 의도된 사용 방식은 다음과 같습니다.

1. 서식을 재사용하고 싶은 자신의 레퍼런스 `.hwpx`를 준비합니다.
2. Rekian으로 구조 프로필을 추출해 `rekian-library`에 캐시합니다.
3. 콘텐츠 자산을 작성한 뒤, 프로필을 기준으로 조립하거나 COM으로 생성합니다.

자기 문서로 돌리는 단계별 워크플로우는 [rekian-library/README.md](rekian-library/README.md)를 참조하세요.

## 저장소 구조

```text
.
├── docs/
│   ├── architecture.md
│   └── publication-scope.md
├── rekian-library/
│   ├── contents/
│   ├── formats/
│   ├── scripts/
│   ├── table_profiles/
│   └── taxonomies/
└── skills/
    ├── hwp-com-writer/
    ├── hwpx-rekian/
    └── rekian-library/
```

## 에이전트 스킬로 설치

스킬 폴더를 에이전트 스킬 디렉터리에 복사하거나 심볼릭 링크로 연결합니다.

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/skills/hwpx-rekian" ~/.codex/skills/hwpx-rekian
ln -s "$(pwd)/skills/hwp-com-writer" ~/.codex/skills/hwp-com-writer
ln -s "$(pwd)/skills/rekian-library" ~/.codex/skills/rekian-library
```

Claude나 Gemini에서는 같은 스킬 폴더를 각 도구의 로컬 스킬 디렉터리에 복사하고, 필요하면 트리거 메타데이터를 맞춰줍니다.

## 요구 사항

순수 HWPX/XML 워크플로우:

- Python 3.10+
- `lxml`

한컴 COM 워크플로우:

- Windows
- 한컴오피스 / 한글(HWP) 설치
- Python 3.10+
- `pywin32`

## 공개 안전 경계

이 저장소는 원본 `.hwp`/`.hwpx` 레퍼런스, 생성 결과물, 미리보기 이미지, 로컬 프로젝트 경로, 생성 캐시를 의도적으로 제외합니다. 라이브러리 자산은 구조·프로필 예시이지 원본 문서의 사본이 아닙니다.

공개 범위 기준은 [docs/publication-scope.md](docs/publication-scope.md)를 참조하세요.

## 크레딧

- [Canine89 / hwpxskill](https://github.com/Canine89/hwpxskill): 공개 HWPX 스킬의 원형
- 공공부문 자동화 커뮤니티 기여자들: 실무 HWP/HWPX 자동화 패턴
- [ai-public-peasant](https://github.com/ai-public-peasant): Rekian 통합, 서식 프로필 워크플로우, COM 핸드오프 설계, 공개 패키징

## 라이선스

MIT. [LICENSE](LICENSE) 참조.
