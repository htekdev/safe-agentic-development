import re

INPUT = r"C:\Repos\htekdev\safe-agentic-development\planning.html"

with open(INPUT, "r", encoding="utf-8") as f:
    content = f.read()

# ── 1. Add highlight.js CDN before </head> ──
hljs_link = '  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/styles/github-dark.min.css">'
hljs_script = '  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.11.1/highlight.min.js"></script>'
content = content.replace("</head>", hljs_link + "\n" + hljs_script + "\n</head>")

# ── 2. Add hljs.highlightAll() before </body> ──
content = content.replace("</body>", "<script>hljs.highlightAll();</script>\n</body>")

# ── 3. Add CSS for highlight.js ──
hljs_css = '    pre code.hljs { background: #161b22; padding: 16px; border-radius: 8px; }\n    .hljs { background: #161b22; }\n\n    /* Code blocks */'
content = content.replace("    /* Code blocks */", hljs_css)

# ── 4. Convert code-block divs to <pre><code> ──
def clean_code_content(inner_html):
    text = inner_html
    text = re.sub(r"<span[^>]*>", "", text)
    text = re.sub(r"</span>", "", text)
    text = re.sub(r"<br\s*/?>", "\n", text)
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&nbsp;", " ")
    return text

def determine_language(text):
    stripped = text.strip()
    if re.search(r"^\s*\$\s", stripped, re.MULTILINE):
        return "bash"
    if re.search(r"^#{1,3}\s", stripped, re.MULTILINE) and (
        "- [ ]" in stripped or "- As a user" in stripped or "## Problem" in stripped
    ):
        return "markdown"
    if stripped.startswith("/plan") or stripped.startswith("/specify"):
        return "plaintext"
    if stripped.startswith("// "):
        return "plaintext"
    if re.search(r"^#\s", stripped, re.MULTILINE):
        return "markdown"
    if "Ctrl+" in stripped or "Shift+" in stripped:
        return "plaintext"
    return "plaintext"

def replacer(m):
    opening_tag = m.group(1)
    inner = m.group(2)

    style_match = re.search(r'style="([^"]*)"', opening_tag)
    div_style = style_match.group(1) if style_match else ""

    plain = clean_code_content(inner)

    # Determine language
    lang = determine_language(plain)

    # Strip leading/trailing blank lines
    lines = plain.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    # Dedent: find minimum indentation
    non_empty = [l for l in lines if l.strip()]
    if non_empty:
        min_indent = min(len(l) - len(l.lstrip()) for l in non_empty)
        if min_indent > 0:
            lines = [l[min_indent:] if len(l) >= min_indent else l for l in lines]
    
    # Remove consecutive blank lines (keep max 1)
    deduped = []
    prev_blank = False
    for line in lines:
        if not line.strip():
            if not prev_blank:
                deduped.append(line)
            prev_blank = True
        else:
            deduped.append(line)
            prev_blank = False
    lines = deduped
    
    plain = "\n".join(lines)

    # HTML-encode for safe embedding in <code>
    plain = plain.replace("&", "&amp;")
    plain = plain.replace("<", "&lt;")
    plain = plain.replace(">", "&gt;")

    # Build style for the <pre> wrapper
    pre_style_parts = []
    for part in div_style.split(";"):
        part = part.strip()
        if not part:
            continue
        if part.startswith("margin") or part.startswith("font-size"):
            pre_style_parts.append(part)
        if part.startswith("border") and ("none" in part or ":0" in part):
            pre_style_parts.append(part)

    pre_style = ' style="' + ";".join(pre_style_parts) + '"' if pre_style_parts else ""

    return '<pre' + pre_style + '><code class="language-' + lang + '">' + plain + "</code></pre>"

pattern = re.compile(
    r'(<div\s+class="code-block"[^>]*>)(.*?)(</div>)',
    re.DOTALL,
)

new_content = pattern.sub(replacer, content)

replaced_count = content.count('class="code-block"') - new_content.count('class="code-block"')
print(f"Replaced {replaced_count} code-block divs")
print(f"Remaining code-block refs: {new_content.count('code-block')}")

# ── 5. Remove old .code-block CSS rules ──
# Remove the .code-block { ... } and .code-block .xxx rules
new_content = re.sub(
    r"\n\s*\.code-block\s+\.[a-z]+\s*\{[^}]*\}",
    "",
    new_content
)
new_content = re.sub(
    r"\s*\.code-block\s*\{[^}]*\}",
    "",
    new_content
)

# ── 6. Write output ──
with open(INPUT, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Done! File written successfully.")
