# Rekian COM Writer Library

Rekian is a public-document redrafting toolkit for HWPX workflows.

This repository bundles three parts that are meant to work together:

- `skills/hwpx-rekian`: reference-driven HWPX redrafting rules and XML utilities
- `skills/hwp-com-writer`: Hancom COM + HWPX XML postprocess backend for high-fidelity generation
- `skills/rekian-library`: skill guide for selecting reusable format and content assets
- `rekian-library`: sanitized format profiles, content examples, table profiles, taxonomies, and composition scripts

The core idea is simple: Rekian reads and classifies a reference document once, stores a sanitized structure/profile in the library, and COM-writer uses that profile as an execution plan when precise Hancom-rendered output matters.

## Repository Layout

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

## Install As Agent Skills

Copy or symlink the skill folders into your agent skill directory.

```bash
mkdir -p ~/.codex/skills
ln -s "$(pwd)/skills/hwpx-rekian" ~/.codex/skills/hwpx-rekian
ln -s "$(pwd)/skills/hwp-com-writer" ~/.codex/skills/hwp-com-writer
ln -s "$(pwd)/skills/rekian-library" ~/.codex/skills/rekian-library
```

For Claude or Gemini, copy the same skill folders into the equivalent local skill directory and adapt the trigger metadata if needed.

## Requirements

Pure HWPX/XML workflows:

- Python 3.10+
- `lxml`

Hancom COM workflows:

- Windows
- Hancom Office / Hangul installed
- Python 3.10+
- `pywin32`

## Public-Safety Boundary

This repository intentionally excludes original `.hwp`/`.hwpx` references, rendered outputs, preview images, local project paths, and generated caches. Library assets are structure/profile examples, not source-document mirrors.

See [docs/publication-scope.md](docs/publication-scope.md) for the publication boundary.

## Credits

- [Canine89 / hwpxskill](https://github.com/Canine89/hwpxskill): original public HWPX skill foundation
- Public-sector automation community contributors: practical HWP/HWPX automation patterns
- [ai-public-peasant](https://github.com/ai-public-peasant): Rekian integration, format-profile workflow, COM handoff design, and public packaging

## License

MIT. See [LICENSE](LICENSE).
