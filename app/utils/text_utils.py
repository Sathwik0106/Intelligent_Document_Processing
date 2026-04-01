import html
import re


def safe_html_text(value: str) -> str:
    return html.escape(value or "").replace("\n", "<br>")


def markdown_to_safe_html(value: str) -> str:
    text = (value or "").replace("\r\n", "\n").strip()
    if not text:
        return ""

    text = re.sub(r"\n(?:\s*[*_]\s*){3,}\n", "\n\n", text)
    text = re.sub(r"^(?:\s*[*_]\s*){3,}$", "", text, flags=re.MULTILINE)

    lines = text.split("\n")
    blocks: list[str] = []
    bullet_items: list[str] = []

    def flush_bullets() -> None:
        nonlocal bullet_items
        if bullet_items:
            blocks.append("<ul>" + "".join(f"<li>{item}</li>" for item in bullet_items) + "</ul>")
            bullet_items = []

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            flush_bullets()
            continue

        bullet_match = re.match(r"^[-*]\s+(.+)$", line)
        if bullet_match:
            bullet_items.append(_format_inline_markdown(bullet_match.group(1)))
            continue

        flush_bullets()
        blocks.append(f"<p>{_format_inline_markdown(line)}</p>")

    flush_bullets()
    return "".join(blocks)


def _format_inline_markdown(value: str) -> str:
    escaped = html.escape(value, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!_)_(?!_)(.+?)(?<!_)_(?!_)", r"<em>\1</em>", escaped)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    return escaped.replace("  ", "&nbsp;&nbsp;")
