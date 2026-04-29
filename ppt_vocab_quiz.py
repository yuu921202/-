from __future__ import annotations

import argparse
import csv
import random
import re
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET


A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PKG_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"

A_P = f"{{{A_NS}}}p"
A_T = f"{{{A_NS}}}t"
A_BR = f"{{{A_NS}}}br"
R_ID = f"{{{R_NS}}}id"

POS_RE = re.compile(
    r"\s+\((?:n|v|adj|adv|ad|a|prep|preposition|conj|pron|abbr|aux|vi|vt|"
    r"p\.p|phr|phrase|pl|sing)[^)]*\)",
    re.IGNORECASE,
)
POS_TOKEN_RE = re.compile(
    r"\((?:n|v|adj|adv|ad|a|prep|preposition|conj|pron|abbr|aux|vi|vt|"
    r"p\.p|phr|phrase|pl|sing)[^)]*\)",
    re.IGNORECASE,
)
MULTISPACE_RE = re.compile(r"\s+")
CJK_RE = re.compile(r"[\u3400-\u9fff]")
CJK_CHUNK_RE = re.compile(r"[\u3400-\u9fff][\u3400-\u9fff、，；;：:（）()／/\s.。…-]*")


@dataclass(frozen=True)
class VocabEntry:
    term: str
    definition: str
    short_definition: str
    source_file: str
    slide_no: int


def configure_output() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def normalize_space(text: str) -> str:
    text = text.replace("\u00a0", " ").replace("\r", "\n")
    text = MULTISPACE_RE.sub(" ", text)
    return text.strip()


def presentation_slide_paths(zf: zipfile.ZipFile) -> list[str]:
    try:
        rels_root = ET.fromstring(zf.read("ppt/_rels/presentation.xml.rels"))
        presentation_root = ET.fromstring(zf.read("ppt/presentation.xml"))
    except KeyError:
        return fallback_slide_paths(zf)

    rel_targets: dict[str, str] = {}
    for rel in rels_root.findall(f".//{{{PKG_REL_NS}}}Relationship"):
        rel_id = rel.attrib.get("Id")
        target = rel.attrib.get("Target", "")
        if rel_id and "slides/" in target and target.endswith(".xml"):
            rel_targets[rel_id] = target

    paths: list[str] = []
    for slide_id in presentation_root.findall(f".//{{{P_NS}}}sldId"):
        rel_id = slide_id.attrib.get(R_ID)
        target = rel_targets.get(rel_id or "")
        if not target:
            continue
        if target.startswith("/"):
            path = target.lstrip("/")
        else:
            path = f"ppt/{target}"
        path = str(Path(path).as_posix())
        if path in zf.namelist():
            paths.append(path)

    return paths or fallback_slide_paths(zf)


def fallback_slide_paths(zf: zipfile.ZipFile) -> list[str]:
    def slide_number(name: str) -> int:
        match = re.search(r"slide(\d+)\.xml$", name)
        return int(match.group(1)) if match else 0

    return sorted(
        [
            name
            for name in zf.namelist()
            if name.startswith("ppt/slides/slide") and name.endswith(".xml")
        ],
        key=slide_number,
    )


def slide_lines(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)
    lines: list[str] = []

    for paragraph in root.iter(A_P):
        chunks: list[str] = []
        for node in paragraph.iter():
            if node.tag == A_T:
                chunks.append(node.text or "")
            elif node.tag == A_BR:
                chunks.append("\n")

        paragraph_text = "".join(chunks)
        for line in paragraph_text.splitlines() or [paragraph_text]:
            clean = normalize_space(line)
            if clean:
                lines.append(clean)

    return lines


def split_term_and_tail(first_line: str) -> tuple[str, str]:
    line = normalize_space(first_line)
    match = POS_RE.search(line)
    if match and match.start() > 0:
        return clean_term(line[: match.start()]), line[match.start() :].strip()
    return clean_term(line), ""


def clean_term(term: str) -> str:
    term = re.sub(r"\[[^\]]+\]", "", term)
    term = normalize_space(term)
    return term.strip(" \t-–—:：|,，.;。")


def looks_like_header(term: str, lines: list[str], tail: str) -> bool:
    lower = term.lower()
    joined = " ".join(lines[:3]).lower()

    if not term or not re.search(r"[A-Za-z]", term):
        return True

    header_patterns = [
        r"^ch\s*\d+\b",
        r"^ch\d+\b",
        r"^chapter\s+\d+\b",
        r"^paragraph\s+\d+\b",
        r"^vocabulary\s*\d",
        r"^key vocabulary\b",
    ]
    if any(re.search(pattern, lower) for pattern in header_patterns):
        return True

    header_words = [
        "pdf",
        "以下單字",
        "出自",
        "順序",
        "課文",
        "主題",
        "techeng",
        "個單字",
        "replaced images",
    ]
    if any(word in joined for word in header_words) and not tail:
        return True

    if len(term) > 70:
        return True

    if CJK_RE.search(term) and not POS_RE.search(lines[0]):
        return True

    if len(lines) < 2 and not tail:
        return True

    return False


def compact_definition(parts: Iterable[str]) -> str:
    text = " ".join(part for part in parts if part)
    text = normalize_space(text)
    text = re.sub(r"\s+([,.;:!?，。；：！？])", r"\1", text)
    return text


def make_short_definition(definition: str, term: str) -> str:
    text = definition
    for marker in ("補充：", "補充:", "例：", "例:", "Ex:", "EX:", "Example:", "example:"):
        if marker in text:
            text = text.split(marker, 1)[0]
    text = normalize_space(text)
    text = POS_TOKEN_RE.sub("", text)
    text = normalize_space(text)

    term_key = term.casefold()
    if term_key:
        first_cjk = CJK_RE.search(text)
        if first_cjk:
            term_after_meaning = text.casefold().find(term_key, first_cjk.start())
            if term_after_meaning != -1:
                cjk_before_term = [
                    match.end()
                    for match in CJK_RE.finditer(text)
                    if match.start() < term_after_meaning
                ]
                if cjk_before_term:
                    text = text[: cjk_before_term[-1]]

    cjk_chunks = [
        normalize_space(chunk).replace("（", "").replace("）", "").replace("(", "").replace(")", "").strip(" ,，.;；。")
        for chunk in CJK_CHUNK_RE.findall(text)
    ]
    cjk_chunks = [chunk for chunk in cjk_chunks if chunk]
    if cjk_chunks:
        return "；".join(cjk_chunks)

    return text.strip(" ;；。")


def extract_from_pptx(path: Path, root: Path) -> list[VocabEntry]:
    entries: list[VocabEntry] = []
    try:
        with zipfile.ZipFile(path) as zf:
            for slide_index, slide_path in enumerate(presentation_slide_paths(zf), start=1):
                lines = slide_lines(zf.read(slide_path))
                if not lines:
                    continue

                term, tail = split_term_and_tail(lines[0])
                if looks_like_header(term, lines, tail):
                    continue

                definition = compact_definition([tail, *lines[1:]])
                if not definition:
                    continue

                entries.append(
                    VocabEntry(
                        term=term,
                        definition=definition,
                        short_definition=make_short_definition(definition, term),
                        source_file=str(path.relative_to(root)),
                        slide_no=slide_index,
                    )
                )
    except zipfile.BadZipFile:
        print(f"略過無法讀取的檔案：{path}", file=sys.stderr)

    return entries


def collect_entries(root: Path) -> list[VocabEntry]:
    def pptx_sort_key(path: Path) -> tuple[int, str]:
        match = re.search(r"ch\s*(\d+)", path.name, re.IGNORECASE)
        chapter = int(match.group(1)) if match else 999
        return chapter, path.name.casefold()

    pptx_files = sorted(root.rglob("*.pptx"), key=pptx_sort_key)
    entries: list[VocabEntry] = []
    for pptx in pptx_files:
        if pptx.name.startswith("~$"):
            continue
        entries.extend(extract_from_pptx(pptx, root))
    return entries


def unique_entries(entries: list[VocabEntry]) -> list[VocabEntry]:
    seen: dict[str, VocabEntry] = {}
    for entry in entries:
        key = normalize_space(entry.term).casefold()
        if key not in seen:
            seen[key] = entry
    return list(seen.values())


def write_csv(path: Path, entries: list[VocabEntry]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.writer(fh)
        writer.writerow(["term", "short_definition", "definition", "source_file", "slide_no"])
        for entry in entries:
            writer.writerow(
                [
                    entry.term,
                    entry.short_definition,
                    entry.definition,
                    entry.source_file,
                    entry.slide_no,
                ]
            )


def escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def write_markdown(path: Path, entries: list[VocabEntry], title: str) -> None:
    with path.open("w", encoding="utf-8-sig") as fh:
        fh.write(f"# {title}\n\n")
        fh.write(f"Total: {len(entries)}\n\n")
        fh.write("| # | Term | Meaning | Source | Slide |\n")
        fh.write("|---:|---|---|---|---:|\n")
        for index, entry in enumerate(entries, start=1):
            fh.write(
                f"| {index} | {escape_md(entry.term)} | {escape_md(entry.short_definition or entry.definition)} | "
                f"{escape_md(entry.source_file)} | {entry.slide_no} |\n"
            )


def write_outputs(entries: list[VocabEntry], out_dir: Path) -> None:
    unique = unique_entries(entries)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_csv(out_dir / "vocabulary_all.csv", entries)
    write_csv(out_dir / "vocabulary_unique.csv", unique)
    write_markdown(out_dir / "vocabulary_all.md", entries, "Vocabulary List - All PPT Entries")
    write_markdown(out_dir / "vocabulary_unique.md", unique, "Vocabulary List - Unique Terms")


def ask_self_grade(entry: VocabEntry, prompt: str, answer: str) -> bool:
    input(f"\n{prompt}\n> ")
    print(f"答案：{answer}")
    result = input("答對嗎？輸入 y 算對，其它鍵算錯：").strip().lower()
    return result == "y"


def run_flashcard_quiz(entries: list[VocabEntry], count: int, reverse: bool) -> None:
    sample = random.sample(entries, k=min(count, len(entries)))
    score = 0

    for index, entry in enumerate(sample, start=1):
        if reverse:
            prompt = f"[{index}/{len(sample)}] 請寫英文單字/片語：{entry.short_definition or entry.definition}"
            answer = entry.term
        else:
            prompt = f"[{index}/{len(sample)}] 請寫中文意思/解釋：{entry.term}"
            answer = entry.definition

        if ask_self_grade(entry, prompt, answer):
            score += 1

    print(f"\n成績：{score}/{len(sample)}")


def run_multiple_choice_quiz(entries: list[VocabEntry], count: int) -> None:
    usable = [entry for entry in entries if entry.short_definition]
    if len(usable) < 4:
        raise SystemExit("可用單字少於 4 個，無法產生選擇題。")

    sample = random.sample(usable, k=min(count, len(usable)))
    score = 0
    labels = ["A", "B", "C", "D"]

    for index, entry in enumerate(sample, start=1):
        distractors = random.sample([item for item in usable if item.term != entry.term], k=3)
        options = [entry, *distractors]
        random.shuffle(options)
        answer_label = labels[options.index(entry)]

        print(f"\n[{index}/{len(sample)}] {entry.short_definition}")
        for label, option in zip(labels, options):
            print(f"  {label}. {option.term}")

        user_answer = input("> ").strip().upper()
        if user_answer == answer_label:
            print("答對！")
            score += 1
        else:
            print(f"答錯。答案是 {answer_label}. {entry.term}")

    print(f"\n成績：{score}/{len(sample)}")


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("必須是正整數")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract vocabulary from PPTX files and run a vocabulary quiz."
    )
    parser.add_argument("--root", default=".", help="PPTX 所在資料夾，預設是目前資料夾")

    subparsers = parser.add_subparsers(dest="command")

    extract_parser = subparsers.add_parser("extract", help="產生單字清單 CSV/Markdown")
    extract_parser.add_argument("--out-dir", default=".", help="輸出資料夾，預設是目前資料夾")

    quiz_parser = subparsers.add_parser("quiz", help="開始互動式單字小考")
    quiz_parser.add_argument("-n", "--count", type=positive_int, default=20, help="題數，預設 20")
    quiz_parser.add_argument(
        "--mode",
        choices=["multiple-choice", "term-to-meaning", "meaning-to-term"],
        default="multiple-choice",
        help="小考模式，預設 multiple-choice",
    )
    quiz_parser.add_argument(
        "--source",
        choices=["unique", "all"],
        default="unique",
        help="使用去重後單字或全部 PPT 條目，預設 unique",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    configure_output()
    parser = build_parser()
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    entries = collect_entries(root)
    if not entries:
        print("找不到可抽取的 .pptx 單字資料。")
        return 1

    if args.command in (None, "extract"):
        out_dir = Path(getattr(args, "out_dir", ".")).resolve()
        write_outputs(entries, out_dir)
        unique_count = len(unique_entries(entries))
        print(f"已抽出 {len(entries)} 筆 PPT 單字條目，去重後 {unique_count} 個。")
        print(f"輸出：{out_dir / 'vocabulary_all.csv'}")
        print(f"輸出：{out_dir / 'vocabulary_unique.csv'}")
        print(f"輸出：{out_dir / 'vocabulary_all.md'}")
        print(f"輸出：{out_dir / 'vocabulary_unique.md'}")
        print("\n開始小考：python ppt_vocab_quiz.py quiz -n 20")
        return 0

    quiz_entries = entries if args.source == "all" else unique_entries(entries)
    random.shuffle(quiz_entries)
    if args.mode == "multiple-choice":
        run_multiple_choice_quiz(quiz_entries, args.count)
    elif args.mode == "meaning-to-term":
        run_flashcard_quiz(quiz_entries, args.count, reverse=True)
    else:
        run_flashcard_quiz(quiz_entries, args.count, reverse=False)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
