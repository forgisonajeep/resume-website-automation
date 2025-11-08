import os
import markdown

def read_text(path):
    """Read a text file and return its contents as a string."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_text(path, text):
    """Write the given text to a file (UTF-8). Create parent folders if needed."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def md_to_html(md_text):
    """Convert Markdown text to HTML using python-markdown."""
    extensions = ["extra", "sane_lists", "toc", "tables", "fenced_code"]
    return markdown.markdown(md_text, extensions=extensions)

def extract_title_from_md(md_text):
    """Return the first H1 line (starts with '# ') without the '# '. Fallback to 'Resume' if none is found."""
    for line in md_text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return "Resume"

def render_page_from_template(template_path, page_title, content_html):
    """Read the HTML template and replace placeholders {{PAGE_TITLE}} and {{CONTENT}}."""
    template = read_text(template_path)
    page = template.replace("{{PAGE_TITLE}}", page_title)
    page = page.replace("{{CONTENT}}", content_html)
    return page

if __name__ == "__main__":
    # Phase 1: read Markdown
    md = read_text("resume.md")

    # Phase 2: simple write test
    write_text("dist/test_output.html", "<h1>Hello from Phase 2!</h1>")

    # Phase 3: convert Markdown → HTML fragment
    html = md_to_html(md)
    write_text("dist/converted.html", html)

    # Phase 4: inject fragment into template → final page
    title = extract_title_from_md(md)
    full_html = render_page_from_template("src/template.html", f"{title} — Resume", html)
    write_text("dist/index.html", full_html)
    print("File written to dist/index.html")
