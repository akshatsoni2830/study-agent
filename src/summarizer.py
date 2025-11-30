from __future__ import annotations

import re
from typing import List, Tuple, Optional


def _extract_section(text: str, heading: str) -> List[str]:
    pattern = re.compile(rf"^##\s+{re.escape(heading)}\s*$", re.IGNORECASE | re.MULTILINE)
    matches = list(pattern.finditer(text))
    if not matches:
        return []
    start = matches[0].end()
    next_heading = re.search(r"^##\s+.+$", text[start:], re.MULTILINE)
    end = start + next_heading.start() if next_heading else len(text)
    section = text[start:end].strip().splitlines()
    return [line.rstrip() for line in section if line.strip()]


def _unique_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out = []
    for i in items:
        key = i.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(i)
    return out


def _extract_algorithm_names(lines: List[str]) -> List[str]:
    import re
    names: List[str] = []
    keywords = (
        "sort", "search", "hash", "tree", "graph", "queue", "stack", "heap",
        "trie", "bfs", "dfs", "dijkstra", "kruskal", "prim", "dp", "dynamic",
        "algorithm", "traversal", "probe", "union", "find"
    )
    for raw in lines:
        s = raw.strip().lstrip("-*").strip()
        if not s:
            continue
        if s.startswith("```"):
            continue
        # skip step lines
        if re.match(r"^(step|algo|algorithm)\s*\d+", s, re.IGNORECASE):
            continue
        # too long -> likely a sentence/step
        if len(s.split()) > 8:
            continue
        low = s.lower()
        if any(k in low for k in keywords):
            # normalize spacing/case: title case common words except acronyms
            title = " ".join([w if w.isupper() else w.capitalize() for w in s.split()])
            if title not in names:
                names.append(title)
    return names


def merge_file_summaries(subject_name: str, file_summaries: List[Tuple[str, str]], semester: Optional[str] = None) -> str:
    overviews: List[str] = []
    key_concepts: List[str] = []
    formulas: List[str] = []
    algorithms_raw: List[str] = []

    for _, summary in file_summaries:
        overviews.extend(_extract_section(summary, "Overview"))
        key_concepts.extend(_extract_section(summary, "Key Concepts (explained like to a kid)"))
        formulas.extend(_extract_section(summary, "Formulas (copy exactly) + one-line meaning"))
        algorithms_raw.extend(_extract_section(summary, "Algorithms (short steps + when to use)"))

    overviews = _unique_preserve_order(overviews)
    key_concepts = _unique_preserve_order(key_concepts)
    formulas = _unique_preserve_order(formulas)
    algorithms_raw = _unique_preserve_order(algorithms_raw)
    algorithm_names = _extract_algorithm_names(algorithms_raw)

    max_points = 14
    simple_points: List[str] = []
    simple_points.extend(overviews[: max_points // 2])
    remaining = max_points - len(simple_points)
    if remaining > 0:
        simple_points.extend(key_concepts[:remaining])
    simple_points = [f"- {p}" if not p.startswith("- ") else p for p in simple_points]

    max_formulas = 8
    formula_points = [f"- {f}" if not f.startswith("- ") else f for f in formulas[:max_formulas]]

    md = []
    title = f"# {subject_name} – Simple Notes"
    if semester and semester.strip():
        title = f"# {subject_name} – {semester.strip()} – Simple Notes"
    md.append(title)
    md.append("")

    # Algorithms section (concise but comprehensive)
    if algorithms_raw:
        md.append("## Algorithms (from all files)")
        # Preserve up to 4 tiny code blocks, and up to 30 bullet/step lines
        alg_lines: List[str] = []
        code_blocks_kept = 0
        inside_code = False
        for line in algorithms_raw:
            ls = line.strip()
            if ls.startswith("```"):
                if not inside_code and code_blocks_kept >= 4:
                    # skip this and subsequent code block
                    inside_code = True
                    continue
                # toggle code block state and keep
                inside_code = not inside_code
                if not inside_code:
                    code_blocks_kept += 1
                alg_lines.append(line)
                continue
            if inside_code:
                # keep code lines if within allowed blocks
                if code_blocks_kept <= 4:
                    alg_lines.append(line)
                continue
            # non-code line: keep concise bullets/steps
            if ls:
                if not ls.startswith(("- ", "* ")):
                    ls = f"- {ls}"
                alg_lines.append(ls)
            if sum(1 for x in alg_lines if x.strip() and not x.strip().startswith("```") ) >= 30 and not inside_code:
                break
        md.extend(alg_lines)
        md.append("")

    # Ensure we don't miss any: list of all algorithm names detected
    if algorithm_names:
        md.append("## All Algorithms Covered (names)")
        md.extend([f"- {n}" for n in algorithm_names])
        md.append("")

    md.append("## Simple Summary (like explaining to a kid)")
    if simple_points:
        md.extend(simple_points)
    else:
        md.append("- This topic covers the big ideas in very simple words.")
    md.append("")

    md.append("## Key Formulas (short list)")
    if formula_points:
        md.extend(formula_points)
    else:
        md.append("- No clear formulas found across the files.")
    md.append("")

    md.append("## Quick Revision")
    if key_concepts:
        md.extend([f"- Review: {c[2:] if c.startswith('- ') else c}" for c in key_concepts[:8]])
    else:
        md.append("- Read the Simple Summary once.")
        md.append("- Remember the 2-3 most important ideas.")

    return "\n".join(md).strip()
