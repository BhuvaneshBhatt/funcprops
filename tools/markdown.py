"""Normalize Markdown prose without rewrapping code, tables or display math."""

import re


def normalize_markdown(text):
    """Keep each paragraph or list item on one line, preserving block syntax."""
    output, paragraph = [], []
    fence = None
    display_math = False

    def flush():
        if paragraph:
            output.append(
                paragraph[0] + "".join(" " + part.strip() for part in paragraph[1:])
            )
            paragraph.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence is not None:
            output.append(line)
            if marker and marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            continue
        if marker:
            flush()
            fence = marker[1]
            output.append(line)
            continue
        if line.strip() in ("$$", r"\[", r"\]"):
            flush()
            display_math = not display_math
            output.append(line)
            continue
        if display_math:
            output.append(line)
            continue
        if not line:
            flush()
            if output and output[-1] != "":
                output.append("")
            continue
        if re.match(r"^\s*(?:#{1,6}\s|\||<!--|>|(?:[-*_]\s*){3,}$)", line):
            flush()
            output.append(line)
            continue
        if re.match(r"^\s*(?:[-+*]|\d+[.)])\s", line):
            flush()
        paragraph.append(line)
    flush()
    return "\n".join(output).rstrip() + "\n"
