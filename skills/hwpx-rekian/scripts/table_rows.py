#!/usr/bin/env python3
"""HWPX 표 행 추가 — 서식 보존 구조 수술 유틸리티.

레퍼런스 서식의 표에 데이터 행을 늘려야 할 때 사용한다.
(예: 사업이 3건인 서식에 7건을 넣어야 할 때)

동작 원리:
  1. 기준 행(after_row)의 <hp:tr>을 복제해 바로 뒤에 삽입
  2. 기준 행에서 시작해 삽입 경계를 넘는 세로병합 셀은 rowSpan을 확장
  3. 삽입 지점 아래 모든 셀의 rowAddr을 밀어냄
  4. hp:tbl rowCnt 갱신, linesegarray 제거(한컴이 열 때 재계산)

복제된 행의 셀 서식(borderFill·폭·높이·글자서식)은 기준 행 것을 그대로 물려받으므로
서식이 깨지지 않는다. 열 병합(colSpan)은 기준 행 그대로 복제된다.

Usage (CLI):
    python table_rows.py input.hwpx --table-index 3 --after-row 1 --count 2 -o out.hwpx
    python table_rows.py input.hwpx --table-index 3 --after-row 1 --count 1 \
        --set "2=새 제안내용" --set "3=비고문구" -o out.hwpx

    --table-index : 문서 전체(섹션 spine 순서)에서 표의 등장 순번 (0-기준)
    --after-row   : 이 행 번호(rowAddr) 뒤에 삽입, 이 행이 복제 원본
    --set COL=TEXT: 새 행의 colAddr=COL 셀에 텍스트 지정 (여러 번 사용 가능,
                    행이 여러 개면 모든 새 행에 동일 적용)

Usage (import):
    from table_rows import insert_rows_in_tree
    inserted = insert_rows_in_tree(section_root, table_index_in_section,
                                   after_row, count, texts={2: "내용"})
"""
from __future__ import annotations

import argparse
import copy
import re
import shutil
import sys
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZIP_STORED, ZipFile

from lxml import etree

NS = {"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}
HP = NS["hp"]


def _addr(tc):
    return tc.find("hp:cellAddr", NS)


def _span(tc):
    return tc.find("hp:cellSpan", NS)


def _cell_cols(tc) -> int:
    return int(_addr(tc).get("colAddr"))


def _set_cell_text(tc, text: str) -> None:
    """셀의 첫 hp:t에 text, 나머지는 비움. hp:t가 없으면 첫 run에 생성."""
    ts = tc.findall(".//hp:t", NS)
    if ts:
        ts[0].text = text
        for n in ts[1:]:
            n.text = ""
        return
    run = tc.find(".//hp:p/hp:run", NS)
    if run is not None:
        etree.SubElement(run, f"{{{HP}}}t").text = text


def insert_rows_in_table(tbl, after_row: int, count: int,
                         texts: dict[int, str] | None = None) -> int:
    """tbl(<hp:tbl>)의 after_row 뒤에 count개 행 삽입. 삽입된 행 수 반환."""
    if count < 1:
        raise ValueError("count는 1 이상이어야 합니다")
    row_cnt = int(tbl.get("rowCnt"))
    if not (0 <= after_row < row_cnt):
        raise ValueError(f"after_row {after_row}가 표 범위(0~{row_cnt-1}) 밖입니다")

    trs = tbl.findall("hp:tr", NS)
    if not trs:  # tr이 하위 깊숙이 있는 변형 구조 방어
        trs = tbl.findall(".//hp:tr", NS)

    template_tr = None
    for tr in trs:
        rows_here = {int(_addr(tc).get("rowAddr")) for tc in tr.findall("hp:tc", NS)}
        if after_row in rows_here:
            template_tr = tr
            break
    if template_tr is None:
        raise ValueError(f"rowAddr {after_row}에서 시작하는 셀이 있는 <hp:tr>을 찾지 못했습니다")

    # 1) 삽입 경계(after_row | after_row+1)를 가로지르는 세로병합 셀 → rowSpan 확장
    boundary_crossers = []
    for tc in tbl.findall(".//hp:tc", NS):
        r = int(_addr(tc).get("rowAddr"))
        rs = int(_span(tc).get("rowSpan"))
        if r <= after_row and (r + rs - 1) >= after_row + 1:
            boundary_crossers.append(tc)
    for tc in boundary_crossers:
        sp = _span(tc)
        sp.set("rowSpan", str(int(sp.get("rowSpan")) + count))

    # 2) 삽입 지점 아래 셀들의 rowAddr 밀어내기 (복제 전에 수행)
    for tc in tbl.findall(".//hp:tc", NS):
        a = _addr(tc)
        if int(a.get("rowAddr")) > after_row:
            a.set("rowAddr", str(int(a.get("rowAddr")) + count))

    # 3) 기준 행 복제: rowSpan이 경계를 넘는 셀(위에서 확장 처리됨)은 복제에서 제외
    parent = template_tr.getparent()
    insert_pos = list(parent).index(template_tr)
    for i in range(1, count + 1):
        new_tr = copy.deepcopy(template_tr)
        for tc in list(new_tr.findall("hp:tc", NS)):
            rs = int(_span(tc).get("rowSpan"))
            if rs != 1:
                # 기준 행에서 시작하는 세로병합 셀: 원본에서 이미 확장됐으므로 복제본에서 제거
                new_tr.remove(tc)
                continue
            _addr(tc).set("rowAddr", str(after_row + i))
            col = _cell_cols(tc)
            _set_cell_text(tc, (texts or {}).get(col, ""))
        if len(new_tr.findall("hp:tc", NS)) == 0:
            raise ValueError("복제할 수 있는 rowSpan=1 셀이 기준 행에 없습니다 — 다른 행을 지정하세요")
        parent.insert(insert_pos + i, new_tr)

    # 4) rowCnt 갱신 + 조판 캐시 제거
    tbl.set("rowCnt", str(row_cnt + count))
    for lsa in tbl.findall(".//hp:linesegarray", NS):
        lsa.getparent().remove(lsa)
    return count


def insert_cols_in_table(tbl, after_col: int, count: int,
                         texts: dict[int, str] | None = None) -> int:
    """after_col 뒤에 count개 열 삽입. 표 전체 폭은 유지(기준 열을 균등 분할).

    texts: {rowAddr: 텍스트} — 새 열의 해당 행 셀에 텍스트 지정.
    """
    if count < 1:
        raise ValueError("count는 1 이상이어야 합니다")
    col_cnt = int(tbl.get("colCnt"))
    if not (0 <= after_col < col_cnt):
        raise ValueError(f"after_col {after_col}가 표 범위(0~{col_cnt-1}) 밖입니다")

    # 1) 경계를 가로지르는 가로병합 셀 → colSpan 확장 (폭 불변: 분할이 자기 영역 안에서 일어남)
    for tc in tbl.findall(".//hp:tc", NS):
        c = int(_addr(tc).get("colAddr"))
        cs = int(_span(tc).get("colSpan"))
        if c <= after_col and (c + cs - 1) >= after_col + 1:
            _span(tc).set("colSpan", str(cs + count))

    # 2) 삽입 지점 오른쪽 셀들 colAddr 밀어내기
    for tc in tbl.findall(".//hp:tc", NS):
        a = _addr(tc)
        if int(a.get("colAddr")) > after_col:
            a.set("colAddr", str(int(a.get("colAddr")) + count))

    # 3) 각 행에서 기준 열 셀 복제 (colSpan=1이고 정확히 after_col에서 시작하는 셀만)
    made = 0
    for tr in tbl.findall(".//hp:tr", NS):
        for tc in tr.findall("hp:tc", NS):
            if int(_addr(tc).get("colAddr")) != after_col:
                continue
            if int(_span(tc).get("colSpan")) != 1:
                continue  # 경계 확장으로 이미 처리됨
            row = int(_addr(tc).get("rowAddr"))
            w = int(tc.find("hp:cellSz", NS).get("width"))
            part = w // (count + 1)
            tc.find("hp:cellSz", NS).set("width", str(w - part * count))
            pos = list(tr).index(tc)
            for i in range(1, count + 1):
                clone = copy.deepcopy(tc)
                _addr(clone).set("colAddr", str(after_col + i))
                clone.find("hp:cellSz", NS).set("width", str(part))
                _set_cell_text(clone, (texts or {}).get(row, ""))
                tr.insert(pos + i, clone)
                made += 1
            break

    tbl.set("colCnt", str(col_cnt + count))
    for lsa in tbl.findall(".//hp:linesegarray", NS):
        lsa.getparent().remove(lsa)
    return made


def merge_cells_in_table(tbl, r1: int, c1: int, r2: int, c2: int) -> None:
    """(r1,c1)~(r2,c2) 직사각형 영역을 하나의 셀로 병합.

    제약: 영역 밖으로 삐져나가는 기존 병합이 있으면 오류.
    영역이 행 전체를 덮어 빈 <hp:tr>이 생기는 병합은 지원하지 않음(행 삭제로 처리할 문제).
    앵커(좌상단) 셀의 내용만 유지되며, 버려지는 셀에 내용이 있으면 오류.
    """
    if r2 < r1 or c2 < c1:
        raise ValueError("영역 좌표가 뒤집혀 있습니다")
    inside, anchor = [], None
    for tc in tbl.findall(".//hp:tc", NS):
        r, c = int(_addr(tc).get("rowAddr")), int(_addr(tc).get("colAddr"))
        rs, cs = int(_span(tc).get("rowSpan")), int(_span(tc).get("colSpan"))
        overlaps = not (r + rs - 1 < r1 or r > r2 or c + cs - 1 < c1 or c > c2)
        if not overlaps:
            continue
        if r < r1 or c < c1 or r + rs - 1 > r2 or c + cs - 1 > c2:
            raise ValueError(f"기존 병합 셀 (r{r},c{c},span{rs}x{cs})이 병합 영역을 벗어납니다")
        inside.append(tc)
        if r == r1 and c == c1:
            anchor = tc
    if anchor is None:
        raise ValueError(f"앵커 셀 (r{r1},c{c1})이 없습니다")
    area = sum(int(_span(tc).get("rowSpan")) * int(_span(tc).get("colSpan")) for tc in inside)
    if area != (r2 - r1 + 1) * (c2 - c1 + 1):
        raise ValueError("영역이 셀로 완전히 덮이지 않습니다 (좌표 확인)")

    # 폭: r1 행에서 영역에 걸친 셀 폭 합 / 높이: c1 열에서 영역에 걸친 셀 높이 합
    width = sum(int(tc.find("hp:cellSz", NS).get("width")) for tc in inside
                if int(_addr(tc).get("rowAddr")) == r1)
    height = sum(int(tc.find("hp:cellSz", NS).get("height")) for tc in inside
                 if int(_addr(tc).get("colAddr")) == c1)

    for tc in inside:
        if tc is anchor:
            continue
        txt = "".join(x.text or "" for x in tc.findall(".//hp:t", NS)).strip()
        if txt:
            raise ValueError(f"버려질 셀 (r{_addr(tc).get('rowAddr')},c{_addr(tc).get('colAddr')})에 내용이 있습니다: {txt[:20]!r}")
        tr = tc.getparent()
        tr.remove(tc)
        if len(tr.findall("hp:tc", NS)) == 0:
            raise ValueError("병합으로 빈 행(<hp:tr>)이 생깁니다 — 이 경우는 행 삭제로 처리하세요")

    _span(anchor).set("rowSpan", str(r2 - r1 + 1))
    _span(anchor).set("colSpan", str(c2 - c1 + 1))
    anchor.find("hp:cellSz", NS).set("width", str(width))
    anchor.find("hp:cellSz", NS).set("height", str(height))
    for lsa in tbl.findall(".//hp:linesegarray", NS):
        lsa.getparent().remove(lsa)


def _iter_section_names(zf: ZipFile) -> list[str]:
    names = [n for n in zf.namelist()
             if re.fullmatch(r"Contents/section\d+\.xml", n)]
    return sorted(names, key=lambda n: int(re.search(r"(\d+)", n).group(1)))


def insert_rows_in_hwpx(src: Path, table_index: int, after_row: int, count: int,
                        texts: dict[int, str] | None, out: Path) -> dict:
    """hwpx 파일 단위 실행. 문서 전체 표 순번(table_index)으로 대상 지정."""
    src, out = Path(src), Path(out)
    with tempfile.TemporaryDirectory() as td:
        work = Path(td) / "pkg"
        with ZipFile(src) as zf:
            zf.extractall(work)
            section_names = _iter_section_names(zf)

        seen = 0
        target_info = None
        for sec_name in section_names:
            sec_path = work / sec_name
            tree = etree.parse(str(sec_path))
            tbls = tree.getroot().findall(".//hp:tbl", NS)
            if table_index < seen + len(tbls):
                tbl = tbls[table_index - seen]
                before = tbl.get("rowCnt")
                insert_rows_in_table(tbl, after_row, count, texts)
                tree.write(str(sec_path), xml_declaration=True,
                           encoding="UTF-8", standalone=True)
                target_info = {"section": sec_name, "rowCnt": f"{before}->{tbl.get('rowCnt')}"}
                break
            seen += len(tbls)
        if target_info is None:
            raise ValueError(f"table_index {table_index}가 문서의 표 개수({seen}) 밖입니다")

        out.unlink(missing_ok=True)
        with ZipFile(out, "w", ZIP_DEFLATED) as z:
            z.write(work / "mimetype", "mimetype", compress_type=ZIP_STORED)
            for f in sorted(work.rglob("*")):
                if f.is_file() and f.name != "mimetype":
                    z.write(f, f.relative_to(work).as_posix())
    return target_info


def main() -> None:
    ap = argparse.ArgumentParser(description="HWPX 표에 서식 보존 행 추가")
    ap.add_argument("input")
    ap.add_argument("--table-index", type=int, required=True,
                    help="문서 전체 기준 표 순번 (0-기준)")
    ap.add_argument("--after-row", type=int, required=True,
                    help="이 rowAddr 뒤에 삽입 (이 행이 복제 원본)")
    ap.add_argument("--count", type=int, default=1)
    ap.add_argument("--set", action="append", default=[], metavar="COL=TEXT",
                    help="새 행의 colAddr=COL 셀 텍스트")
    ap.add_argument("-o", "--output", required=True)
    args = ap.parse_args()

    texts = {}
    for item in getattr(args, "set"):
        col, _, val = item.partition("=")
        texts[int(col)] = val

    info = insert_rows_in_hwpx(Path(args.input), args.table_index,
                               args.after_row, args.count, texts, Path(args.output))
    print(f"OK: {info['section']} 표 행 {info['rowCnt']} → {args.output}")


if __name__ == "__main__":
    main()
