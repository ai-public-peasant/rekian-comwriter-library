from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile


TEXT_RE = re.compile(r"<[^>]*:t(?:\s[^>]*)?>(.*?)</[^>]*:t>", re.S)
TAG_RE = re.compile(r"<[^>]+>")

OFFICIAL_LETTER_FIELDS = [
    {"key": "organization_name", "label": "기관명", "required": True, "zone": "header"},
    {"key": "recipient", "label": "수신", "required": True, "zone": "header"},
    {"key": "via", "label": "경유", "required": False, "zone": "header"},
    {"key": "subject", "label": "제목", "required": True, "zone": "header"},
    {"key": "body", "label": "본문", "required": True, "zone": "body"},
    {"key": "attachments", "label": "붙임", "required": False, "zone": "body"},
    {"key": "drafter", "label": "담당자", "required": False, "zone": "approval"},
    {"key": "division_chair", "label": "분과위원장", "required": False, "zone": "approval"},
    {"key": "committee_chair", "label": "인수위원장", "required": False, "zone": "approval"},
    {"key": "approval_date", "label": "결재일자", "required": False, "zone": "approval"},
    {"key": "document_number", "label": "시행번호", "required": False, "zone": "footer"},
    {"key": "issue_date", "label": "시행일자", "required": False, "zone": "footer"},
    {"key": "postal_code", "label": "우편번호", "required": False, "zone": "footer"},
    {"key": "address", "label": "주소", "required": False, "zone": "footer"},
    {"key": "phone", "label": "전화번호", "required": False, "zone": "footer"},
    {"key": "fax", "label": "팩스번호", "required": False, "zone": "footer"},
    {"key": "email", "label": "이메일", "required": False, "zone": "footer"},
    {"key": "disclosure", "label": "공개구분", "required": False, "zone": "footer"},
]

LABEL_PATTERNS = {
    "organization_name": [r"위원회$", r"시장직.*인수위원회"],
    "recipient": [r"수신"],
    "via": [r"경유"],
    "subject": [r"제목"],
    "attachments": [r"붙임", r"첨부"],
    "drafter": [r"담당자", r"기안"],
    "division_chair": [r"분과위원장"],
    "committee_chair": [r"인수위원장"],
    "approval_date": [r"결재"],
    "document_number": [r"시행"],
    "issue_date": [r"시행"],
    "phone": [r"전화", r"TEL"],
    "fax": [r"팩스", r"FAX"],
    "email": [r"@", r"이메일", r"mail"],
    "disclosure": [r"공개", r"비공개"],
}

ZONE_RULES = [
    ("header", ["organization_name", "recipient", "via", "subject"]),
    ("body", ["body", "attachments"]),
    ("approval", ["drafter", "division_chair", "committee_chair", "approval_date"]),
    ("footer", ["document_number", "issue_date", "phone", "fax", "email", "disclosure"]),
]


def read_zip_text(zf: ZipFile, name: str) -> str:
    raw = zf.read(name)
    for encoding in ("utf-8", "utf-16", "cp949"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def clean_text(text: str) -> str:
    text = TAG_RE.sub("", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def extract_hwpx_text_nodes(xml: str) -> list[str]:
    nodes = [clean_text(match.group(1)) for match in TEXT_RE.finditer(xml)]
    return [node for node in nodes if node]


def count_tag(xml: str, tag: str) -> int:
    return len(re.findall(rf"<(?!/)[^>]*:{re.escape(tag)}\b", xml))


def extract_attrs(xml: str, tag: str, limit: int = 20) -> list[dict[str, str]]:
    attrs_list: list[dict[str, str]] = []
    pattern = re.compile(rf"<(?!/)[^>]*:{re.escape(tag)}\b([^>]*)>", re.S)
    for match in pattern.finditer(xml):
        attrs = {
            key: value
            for key, value in re.findall(r'([A-Za-z_:.-]+)="([^"]*)"', match.group(1))
        }
        attrs_list.append(attrs)
        if len(attrs_list) >= limit:
            break
    return attrs_list


def infer_slots(text_nodes: list[str]) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    seen: set[tuple[str, int]] = set()
    for index, text in enumerate(text_nodes):
        for key, patterns in LABEL_PATTERNS.items():
            if any(re.search(pattern, text, re.I) for pattern in patterns):
                marker = (key, index)
                if marker in seen:
                    continue
                seen.add(marker)
                found.append(
                    {
                        "key": key,
                        "node_index": index,
                        "label_hint": text[:80],
                        "context_before": text_nodes[index - 1][:80] if index > 0 else "",
                        "context_after": text_nodes[index + 1][:80] if index + 1 < len(text_nodes) else "",
                    }
                )
    return found


def infer_document_type(text_nodes: list[str], slots: list[dict[str, object]]) -> str:
    keys = {str(slot["key"]) for slot in slots}
    if {"recipient", "subject"} <= keys and ("document_number" in keys or "approval_date" in keys):
        return "official_letter"
    joined = " ".join(text_nodes[:120])
    if "수신" in joined and "제목" in joined:
        return "official_letter"
    return "document_format"


def build_zone_map(slots: list[dict[str, object]]) -> dict[str, list[dict[str, object]]]:
    by_key: dict[str, list[dict[str, object]]] = {}
    for slot in slots:
        by_key.setdefault(str(slot["key"]), []).append(slot)

    zone_map: dict[str, list[dict[str, object]]] = {}
    for zone, keys in ZONE_RULES:
        zone_entries: list[dict[str, object]] = []
        for key in keys:
            zone_entries.extend(by_key.get(key, []))
        zone_map[zone] = sorted(zone_entries, key=lambda item: int(item["node_index"]))
    return zone_map


def structure_fingerprint(payload: dict[str, object]) -> str:
    serial = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serial.encode("utf-8")).hexdigest()


def analyze_hwpx(input_path: Path) -> dict[str, object]:
    with ZipFile(input_path) as zf:
        names = zf.namelist()
        section_names = sorted(
            name
            for name in names
            if name.startswith("Contents/section") and name.endswith(".xml")
        )
        header_xml = read_zip_text(zf, "Contents/header.xml") if "Contents/header.xml" in names else ""
        sections = {name: read_zip_text(zf, name) for name in section_names}
        text_nodes: list[str] = []
        section_summaries: list[dict[str, object]] = []

        for name, xml in sections.items():
            section_texts = extract_hwpx_text_nodes(xml)
            text_nodes.extend(section_texts)
            section_summaries.append(
                {
                    "path": name,
                    "paragraph_count": count_tag(xml, "p"),
                    "run_count": count_tag(xml, "run"),
                    "text_node_count": count_tag(xml, "t"),
                    "non_empty_text_node_count": len(section_texts),
                    "table_count": count_tag(xml, "tbl"),
                    "cell_count": count_tag(xml, "tc"),
                    "picture_count": count_tag(xml, "pic"),
                    "container_paragraph_count": len(
                        re.findall(r"<(?!/)[^>]*:p\b(?:(?!</[^>]*:p>).)*<(?!/)[^>]*:tbl\b", xml, re.S)
                    ),
                }
            )

        bindata = [name for name in names if name.startswith("BinData/")]
        previews = [name for name in names if name.startswith("Preview/")]
        slots = infer_slots(text_nodes)
        doc_type = infer_document_type(text_nodes, slots)

        structure = {
            "package_type": "hwpx",
            "section_count": len(section_names),
            "sections": section_summaries,
            "header": {
                "charPr_count": count_tag(header_xml, "charPr"),
                "paraPr_count": count_tag(header_xml, "paraPr"),
                "style_count": count_tag(header_xml, "style"),
                "borderFill_count": count_tag(header_xml, "borderFill"),
                "fontface_count": count_tag(header_xml, "fontface"),
                "page_def_samples": extract_attrs(header_xml, "pageDef", limit=5),
                "charPr_samples": extract_attrs(header_xml, "charPr", limit=10),
                "borderFill_samples": extract_attrs(header_xml, "borderFill", limit=10),
            },
            "resources": {
                "bindata_count": len(bindata),
                "bindata_names": bindata,
                "preview_files": previews,
            },
            "text": {
                "non_empty_text_node_count": len(text_nodes),
                "first_label_like_nodes": [
                    slot["label_hint"]
                    for slot in sorted(slots, key=lambda item: int(item["node_index"]))[:40]
                ],
            },
        }

    return {
        "document_type": doc_type,
        "structure": structure,
        "slots": slots,
        "zone_map": build_zone_map(slots),
        "fingerprint": structure_fingerprint(structure),
    }


def analyze_odt(input_path: Path) -> dict[str, object]:
    with ZipFile(input_path) as zf:
        names = zf.namelist()
        content_xml = read_zip_text(zf, "content.xml")

    text_nodes = [
        clean_text(match.group(1))
        for match in re.finditer(r"<text:[^>]+\b[^>]*>(.*?)</text:[^>]+>", content_xml, re.S)
    ]
    text_nodes = [node for node in text_nodes if node]
    slots = infer_slots(text_nodes)
    doc_type = infer_document_type(text_nodes, slots)
    structure = {
        "package_type": "odt",
        "content_xml": {
            "paragraph_count": len(re.findall(r"<text:p\b", content_xml)),
            "heading_count": len(re.findall(r"<text:h\b", content_xml)),
            "table_count": len(re.findall(r"<table:table\b", content_xml)),
            "row_count": len(re.findall(r"<table:table-row\b", content_xml)),
            "cell_count": len(re.findall(r"<table:table-cell\b", content_xml)),
            "image_count": len(re.findall(r"<draw:image\b", content_xml)),
            "frame_count": len(re.findall(r"<draw:frame\b", content_xml)),
        },
        "resources": {
            "package_file_count": len(names),
            "picture_files": [name for name in names if name.startswith("Pictures/")],
        },
        "text": {
            "non_empty_text_node_count": len(text_nodes),
            "first_label_like_nodes": [
                slot["label_hint"]
                for slot in sorted(slots, key=lambda item: int(item["node_index"]))[:40]
            ],
        },
    }
    return {
        "document_type": doc_type,
        "structure": structure,
        "slots": slots,
        "zone_map": build_zone_map(slots),
        "fingerprint": structure_fingerprint(structure),
    }


def placeholder_schema(document_type: str) -> dict[str, object]:
    if document_type == "official_letter":
        fields = OFFICIAL_LETTER_FIELDS
    else:
        fields = [
            {"key": "title", "label": "제목", "required": True, "zone": "header"},
            {"key": "body", "label": "본문", "required": True, "zone": "body"},
            {"key": "attachments", "label": "붙임", "required": False, "zone": "body"},
        ]
    return {
        "schema_version": "0.1.0",
        "document_type": document_type,
        "fields": fields,
        "content_contract": {
            "input_format": "json",
            "writer": "hwp-com-writer",
            "rule": "Fill values by semantic key. Preserve source layout objects and only replace visible text slots unless explicitly rebuilding.",
        },
    }


def write_json(path: Path, data: dict[str, object]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_format_json(
    format_id: str,
    label: str,
    description: str,
    document_type: str,
    profile_path: str,
    schema_path: str,
) -> dict[str, object]:
    return {
        "id": format_id,
        "label": label,
        "description": description,
        "status": "profile-cache",
        "sanitized_source": True,
        "document_type": document_type,
        "profile": profile_path,
        "placeholder_schema": schema_path,
        "workflow": {
            "reader": "hwpx-rekian",
            "writer": "hwp-com-writer",
            "mode": "profile_first_then_com",
        },
        "notes": [
            "This asset stores read format information, not the original source document.",
            "Use format_profile.json for structure and slot detection before re-reading a raw reference.",
            "Use placeholder_schema.json as the handoff contract for COM generation.",
        ],
    }


def write_readme(path: Path, label: str, source_path: Path, document_type: str) -> None:
    text = f"""# {label}

This Rekian format asset stores read format information only.

- Source reference: `{source_path}`
- Document type: `{document_type}`
- Profile: `format_profile.json`
- Handoff schema: `placeholder_schema.json`
- Reader: `hwpx-rekian`
- Writer: `hwp-com-writer`

Do not store the original source file or preview images in this format asset unless a sanitized template is intentionally created.
"""
    path.write_text(text, encoding="utf-8")


def create_profile(
    repo_root: Path,
    input_path: Path,
    format_id: str,
    label: str,
    description: str,
    force: bool,
) -> Path:
    if input_path.suffix.lower() == ".hwpx":
        analysis = analyze_hwpx(input_path)
    elif input_path.suffix.lower() == ".odt":
        analysis = analyze_odt(input_path)
    else:
        raise ValueError(f"Unsupported input type: {input_path.suffix}")

    output_dir = repo_root / "formats" / format_id
    output_dir.mkdir(parents=True, exist_ok=True)
    profile_path = output_dir / "format_profile.json"
    schema_path = output_dir / "placeholder_schema.json"
    format_path = output_dir / "format.json"
    readme_path = output_dir / "README.md"

    for path in (profile_path, schema_path, format_path, readme_path):
        if path.exists() and not force:
            raise FileExistsError(f"{path} exists. Use --force to overwrite.")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    profile = {
        "schema_version": "0.1.0",
        "format_id": format_id,
        "label": label,
        "description": description,
        "generated_at": generated_at,
        "source_audit": {
            "source_path": str(input_path),
            "source_suffix": input_path.suffix.lower(),
            "source_size_bytes": input_path.stat().st_size,
            "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
            "source_file_copied": False,
        },
        "handoff": {
            "reader": "hwpx-rekian",
            "writer": "hwp-com-writer",
            "load_order": [
                "formats/<format-id>/format.json",
                "formats/<format-id>/format_profile.json",
                "formats/<format-id>/placeholder_schema.json",
            ],
            "speed_rule": "Use cached structure first. Re-open the raw reference only when the profile lacks a required slot or visual verification fails.",
        },
        **analysis,
    }
    schema = placeholder_schema(str(analysis["document_type"]))
    format_json = build_format_json(
        format_id=format_id,
        label=label,
        description=description,
        document_type=str(analysis["document_type"]),
        profile_path="format_profile.json",
        schema_path="placeholder_schema.json",
    )

    write_json(profile_path, profile)
    write_json(schema_path, schema)
    write_json(format_path, format_json)
    write_readme(readme_path, label, input_path, str(analysis["document_type"]))
    return output_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract a reusable Rekian format profile")
    parser.add_argument("--input", required=True, help="Source .hwpx or .odt reference")
    parser.add_argument("--format-id", required=True, help="Library format id")
    parser.add_argument("--label", required=True, help="Human label")
    parser.add_argument("--description", required=True, help="Short description")
    parser.add_argument("--force", action="store_true", help="Overwrite existing generated profile files")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output_dir = create_profile(
        repo_root=repo_root,
        input_path=Path(args.input).resolve(),
        format_id=args.format_id,
        label=args.label,
        description=args.description,
        force=args.force,
    )
    print(f"Wrote Rekian format profile: {output_dir}")


if __name__ == "__main__":
    main()
