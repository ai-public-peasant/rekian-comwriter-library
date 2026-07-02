from __future__ import annotations

import argparse
import json
import shutil
import stat
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree


NS = {
    "hp": "http://www.hancom.co.kr/hwpml/2011/paragraph",
    "opf": "http://www.idpf.org/2007/opf/",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(data: object, path: str) -> object:
    current = data
    for part in path.split("."):
        name = part
        indexes: list[int] = []
        while "[" in name:
            base = name[: name.index("[")]
            index = int(name[name.index("[") + 1 : name.index("]")])
            name = name[name.index("]") + 1 :]
            if base:
                current = current[base]
                base = ""
            indexes.append(index)
        if name:
            current = current[name]
        for index in indexes:
            current = current[index]
    return current


def binding_value(binding: dict, content: dict) -> str:
    if "literal" in binding:
        return str(binding["literal"])
    if "from" in binding:
        return str(resolve_path(content, binding["from"]))
    raise KeyError(f"Unsupported binding: {binding}")


def replace_text_nodes(section_path: Path, bindings: list[dict], content: dict) -> None:
    tree = etree.parse(str(section_path))
    root = tree.getroot()
    text_nodes = [
        node
        for node in root.findall(".//hp:t", NS)
        if node.text and node.text.strip()
    ]

    if len(text_nodes) != len(bindings):
        raise RuntimeError(
            f"Binding count mismatch: section has {len(text_nodes)} nodes, format has {len(bindings)} bindings"
        )

    for node, binding in zip(text_nodes, bindings, strict=True):
        node.text = binding_value(binding, content)

    # Force Hancom to recompute line layout after content injection.
    for lineseg in root.findall(".//hp:linesegarray", NS):
        parent = lineseg.getparent()
        if parent is not None:
            parent.remove(lineseg)

    tree.write(
        str(section_path),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def update_metadata(content_hpf: Path, format_data: dict, content: dict) -> None:
    tree = etree.parse(str(content_hpf))
    root = tree.getroot()

    title_key = format_data["metadata"]["title_from"]
    title_text = str(resolve_path(content, title_key)).strip()
    creator_text = format_data["metadata"].get("creator", "rekian-library")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    title_el = root.find(".//opf:title", NS)
    if title_el is not None:
        title_el.text = title_text

    for meta in root.findall(".//opf:meta", NS):
        name = meta.get("name", "")
        if name == "creator":
            meta.text = creator_text
        elif name == "lastsaveby":
            meta.text = creator_text
        elif name in {"CreatedDate", "ModifiedDate"}:
            meta.text = now

    tree.write(
        str(content_hpf),
        encoding="UTF-8",
        xml_declaration=True,
        pretty_print=True,
    )


def update_preview(preview_path: Path, preview_bindings: list[dict], content: dict) -> None:
    lines = [binding_value(binding, content).strip() for binding in preview_bindings]
    preview_path.write_text("\n".join(lines), encoding="utf-8")


def pack_hwpx(input_dir: Path, output_path: Path) -> None:
    mimetype_file = input_dir / "mimetype"
    if not mimetype_file.is_file():
        raise FileNotFoundError(f"Missing mimetype file in {input_dir}")

    all_files = sorted(
        path.relative_to(input_dir).as_posix()
        for path in input_dir.rglob("*")
        if path.is_file()
    )

    with ZipFile(output_path, "w", ZIP_DEFLATED) as zf:
        zf.write(mimetype_file, "mimetype", compress_type=ZIP_STORED)
        for rel_path in all_files:
            if rel_path == "mimetype":
                continue
            zf.write(input_dir / rel_path, rel_path, compress_type=ZIP_DEFLATED)


def remove_readonly(func, path, _exc_info) -> None:
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def safe_reset_dir(path: Path, allowed_parent: Path) -> None:
    if path.exists():
        resolved = path.resolve()
        if resolved.parent != allowed_parent.resolve():
            raise RuntimeError(f"Refusing to delete unexpected directory: {resolved}")
        shutil.rmtree(resolved, onerror=remove_readonly)
    path.mkdir(parents=True, exist_ok=True)


def compose(repo_root: Path, format_id: str, content_id: str, output_path: Path | None) -> Path:
    format_path = repo_root / "formats" / format_id / "format.json"
    content_path = repo_root / "contents" / content_id / "content.json"
    format_data = load_json(format_path)
    content = load_json(content_path)

    unpacked_dir = repo_root / format_data["unpacked_dir"]
    build_dir = repo_root / "outputs" / f"{format_id}__{content_id}"
    safe_reset_dir(build_dir, repo_root / "outputs")
    shutil.copytree(unpacked_dir, build_dir, dirs_exist_ok=True)

    section_path = build_dir / format_data["paths"]["section_xml"]
    content_hpf_path = build_dir / format_data["paths"]["content_hpf"]
    preview_path = build_dir / format_data["paths"]["preview_text"]

    replace_text_nodes(section_path, format_data["text_bindings"], content)
    update_metadata(content_hpf_path, format_data, content)
    update_preview(preview_path, format_data["preview_bindings"], content)

    if output_path is None:
        output_path = repo_root / "outputs" / f"{format_id}__{content_id}.hwpx"
    pack_hwpx(build_dir, output_path)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Compose HWPX from rekian format and content assets")
    parser.add_argument("--format", required=True, dest="format_id", help="Format asset id")
    parser.add_argument("--content", required=True, dest="content_id", help="Content asset id")
    parser.add_argument("--output", help="Optional output .hwpx path")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    output_path = Path(args.output).resolve() if args.output else None
    result = compose(repo_root, args.format_id, args.content_id, output_path)
    print(f"Composed: {result}")


if __name__ == "__main__":
    main()
