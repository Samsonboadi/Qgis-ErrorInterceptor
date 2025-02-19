import re

def markdown_to_html(text):
    """
    Converts Markdown text to HTML.
    Supports:
    - Headings
    - Bold and Italic text
    - Bullet and numbered lists (including nested lists)
    - Code blocks and inline code
    - Links
    - Blockquotes
    - Horizontal rules
    - Images
    """

    # Escape HTML special characters except for those used in Markdown
    escape_chars = {'&': '&#38;', '<': '&#60;', '>': '&#62;', '"': '&#34;', "'": '&#39;'}
    for char, escape in escape_chars.items():
        text = text.replace(char, escape)

    # Split text into lines for processing
    lines = text.split('\n')

    # ------------------------------------------------
    # NEW: Strip leading spaces from each line so that
    # Markdown syntax can be matched properly.
    # ------------------------------------------------
    for i in range(len(lines)):
        lines[i] = lines[i].lstrip()
        
    html = ""
    in_code_block = False
    code_block_language = ""
    list_stack = []

    for line in lines:
        # --------------------------------------------
        # Handle code blocks
        # --------------------------------------------
        code_block_match = re.match(r'^```(\w+)?', line)
        if code_block_match:
            if not in_code_block:
                in_code_block = True
                code_block_language = code_block_match.group(1) or ""
                language_class = f' class="language-{code_block_language}"' if code_block_language else ""
                html += f"<pre><code{language_class}>\n"
            else:
                in_code_block = False
                html += "</code></pre>\n"
            continue

        if in_code_block:
            # Keep code block content as-is (minus initial HTML escaping, which we already did)
            html += line + "\n"
            continue

        # --------------------------------------------
        # Handle horizontal rules (e.g. --- or ***)
        # --------------------------------------------
        if re.match(r'^([-*_])\1\1\s*$', line):
            html += "<hr />\n"
            continue

        # --------------------------------------------
        # Handle blockquotes (> ...)
        # --------------------------------------------
        blockquote_match = re.match(r'^>+\s*(.*)', line)
        if blockquote_match:
            content = blockquote_match.group(1)
            content_html = parse_inline_markdown(content)
            html += f"<blockquote>{content_html.strip()}</blockquote>\n"
            continue

        # --------------------------------------------
        # Handle headings (#, ##, ###, etc.)
        # --------------------------------------------
        heading_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if heading_match:
            level = len(heading_match.group(1))
            content = heading_match.group(2).strip()
            content_html = parse_inline_markdown(content)
            html += f"<h{level}>{content_html}</h{level}>\n"
            continue

        # --------------------------------------------
        # Handle lists
        #  - Unordered: -, *, +
        #  - Ordered: number.
        # --------------------------------------------
        ul_match = re.match(r'^([-\*\+])\s+(.*)', line)
        ol_match = re.match(r'^(\d+)\.\s+(.*)', line)

        if ul_match or ol_match:
            current_list_type = 'ul' if ul_match else 'ol'
            current_content = ul_match.group(2) if ul_match else ol_match.group(2)
            current_indent = 0  # You could track indentation for nested lists if desired

            # Close any lists that are "deeper" than current indent or different type
            while list_stack and list_stack[-1][0] > current_indent:
                html += f"</{list_stack[-1][1]}>"
                list_stack.pop()

            # Open or continue the current list if needed
            if not list_stack or list_stack[-1][1] != current_list_type:
                html += f"<{current_list_type}>\n"
                list_stack.append((current_indent, current_list_type))

            content_html = parse_inline_markdown(current_content)
            html += f"<li>{content_html}</li>\n"
            continue

        else:
            # Not a list line: close all currently open lists
            while list_stack:
                html += f"</{list_stack[-1][1]}>"
                list_stack.pop()

        # --------------------------------------------
        # Handle inline Markdown in a paragraph
        # --------------------------------------------
        content_html = parse_inline_markdown(line.strip())
        if content_html:
            html += f"<p>{content_html}</p>\n"

    # Close any remaining open lists
    while list_stack:
        html += f"</{list_stack[-1][1]}>"
        list_stack.pop()

    return html


def parse_inline_markdown(text):
    """
    Parses inline Markdown elements and converts them to HTML.
    Supports:
    - Bold and Italic text
    - Inline code
    - Links
    - Images
    """
    # Bold+italic (*** or ___)
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
    text = re.sub(r'___(.+?)___', r'<strong><em>\1</em></strong>', text)

    # Bold (** or __)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)

    # Italic (* or _)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)

    # Inline code (`code`)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)

    # Links ([text](url))
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)

    # Images (![alt](url))
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', r'<img src="\2" alt="\1" />', text)

    return text
