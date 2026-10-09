#!/usr/bin/env python3
"""Build the training website (index.html) from the slide deck.

The deck in source/odoo-workflow-slides.html is the single source of truth:
every slide's content is reused as-is, and this script only re-wraps it into
a scrollable, responsive page with chapter navigation.

    python3 tools/build_site.py
"""
import re
from pathlib import Path

from bs4 import BeautifulSoup, Comment

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "source" / "odoo-workflow-slides.html"
OUT = ROOT / "index.html"
SLIDES_OUT = ROOT / "slides.html"
LOGO = "https://www.images.cybrosys.com/images/cybro-logo-color.png"

# (first slide number, chapter title, short description) — slide numbers are
# 1-based positions in the deck. A chapter runs until the next one starts.
CHAPTERS = [
    (3, "Odoo Fundamentals", "Version · Edition · Hosting · Lifecycle · Architecture"),
    (13, "Accounting Basics", "Assets · Liabilities · Debit & Credit"),
    (19, "Odoo Accounting", "CoA · Journals · Payments · Reconciliation"),
    (26, "Invoicing Module", "Invoice creation to payment"),
    (29, "Accounting Module", "Setup to compliance"),
    (32, "Accounting Standards", "Anglo-Saxon · Continental · GAAP · IFRS"),
    (37, "Accounting Reports", "12 essential reports"),
    (50, "Complete Workflow", "Product types · Routes · Documents"),
    (59, "CRM", "Lead to closed deal"),
    (62, "Sales", "Quotation to payment"),
    (65, "Purchase", "RFQ to payment"),
    (68, "Inventory", "Warehouse · Stock movements"),
    (71, "Manufacturing", "BOM · MO · Production"),
    (74, "Projects", "Tasks · Timesheets · Service flow"),
    (79, "Point of Sale", "Sessions · Orders · Close"),
    (82, "Employees", "Joining to exit"),
    (85, "Email Marketing", "Contacts to automation"),
    (88, "Odoo Studio", "No-code customization"),
    (90, "Installation Guide", "Run Odoo on localhost"),
    (93, "Settings", "The control center"),
    (96, "Real Client Scenarios", "Trading · Manufacturing · Service"),
    (100, "Implementation Mindset", "Think like a consultant"),
]


def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def clean(node):
    """Drop slide-only chrome: comments, corner logos, 'Press →' hints, zoom."""
    for c in node.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()
    for img in node.find_all("img"):
        parent = img.parent
        if parent is not None and "position:absolute" in (parent.get("style") or ""):
            parent.decompose()
    for div in node.find_all("div"):
        if div.get_text(strip=True).startswith("Press →"):
            div.decompose()
    for div in node.find_all("div"):
        if div.get_text(strip=True) == "→" and not div.find("div"):
            div["class"] = div.get("class", []) + ["arr"]
    for el in node.find_all(style=True):
        style = re.sub(r"zoom:[0-9.]+;?", "", el["style"]).strip()
        if style:
            el["style"] = style
        else:
            del el["style"]
    return node


def render_topic(slide, num, prefix):
    title = slide.select_one(".hdr-title").get_text(strip=True)
    sub = slide.select_one(".hdr-sub")
    body = clean(slide.select_one(".body"))
    # The wrapper's inline style only sized the content to a 1280×720 slide;
    # keep just whether it laid its children out side by side.
    style = body.attrs.pop("style", "")
    is_row = "display:flex" in style and "flex-direction:column" not in style
    body["class"] = ["topic-body"] + (["topic-row"] if is_row else [])
    anchor = f"{prefix}--{slugify(title)}"
    sub_html = f'<p class="topic-sub">{sub.decode_contents()}</p>' if sub else ""
    return anchor, title, (
        f'<article class="topic" id="{anchor}">'
        f'<header class="topic-hdr"><span class="topic-num">{num:02d}</span>'
        f'<div><h3>{slide.select_one(".hdr-title").decode_contents()}</h3>{sub_html}</div></header>'
        f"{body}</article>"
    )


def render_banner(slide):
    inner = clean(slide.find("div", recursive=False))
    inner["class"] = ["banner"]
    return str(inner)


def main():
    soup = BeautifulSoup(SRC.read_text(encoding="utf-8"), "html.parser")
    slides = soup.select(".deck > .slide")
    deck_css = soup.find("style").string
    # Keep only the content styles from the deck; layout/nav rules are replaced.
    deck_css = deck_css.split("/* nav */")[0] + deck_css.split("/* section divider slide */")[1]

    starts = {start: i for i, (start, *_) in enumerate(CHAPTERS)}
    chapters_html, nav_html = [], []
    current = None
    topic_no = 0
    for num, slide in enumerate(slides, 1):
        if num in (1, 2, len(slides)):
            continue  # hero, agenda and closing are rebuilt below
        if num in starts:
            if current:
                chapters_html.append(current)
            idx = starts[num]
            _, name, desc = CHAPTERS[idx]
            cid = f"ch-{idx + 1:02d}-{slugify(name)}"
            current = {"id": cid, "idx": idx + 1, "name": name, "desc": desc, "parts": [], "topics": []}
            if slide.select_one(".hdr-title") is None:
                current["parts"].append(render_banner(slide))
                continue
            current["parts"].append(
                f'<div class="banner banner-plain"><div class="banner-kicker">Chapter {idx + 1:02d}</div>'
                f"<h2>{name}</h2><p>{desc}</p></div>"
            )
        if slide.select_one(".hdr-title") is None:
            current["parts"].append(render_banner(slide))
            continue
        topic_no += 1
        anchor, title, html = render_topic(slide, topic_no, current["id"])
        current["parts"].append(html)
        current["topics"].append((anchor, title))
    chapters_html.append(current)

    sections, cards = [], []
    for ch in chapters_html:
        sections.append(
            f'<section class="chapter" id="{ch["id"]}" data-chapter="{ch["idx"]}">'
            + "".join(ch["parts"]) + "</section>"
        )
        links = "".join(f'<li><a href="#{a}">{t}</a></li>' for a, t in ch["topics"])
        nav_html.append(
            f'<li class="nav-ch" data-chapter="{ch["idx"]}"><a class="nav-ch-link" href="#{ch["id"]}">'
            f'<span>{ch["idx"]:02d}</span>{ch["name"]}</a><ul>{links}</ul></li>'
        )
        cards.append(
            f'<a class="ov-card" href="#{ch["id"]}"><span class="ov-num">{ch["idx"]:02d}</span>'
            f'<span class="ov-name">{ch["name"]}</span><span class="ov-desc">{ch["desc"]}</span>'
            f'<span class="ov-count">{len(ch["topics"])} topic{"s" if len(ch["topics"]) != 1 else ""}</span></a>'
        )

    closing = render_banner(slides[-1])
    template = (ROOT / "tools" / "site_template.html").read_text(encoding="utf-8")
    page = (
        template.replace("{{DECK_CSS}}", deck_css)
        .replace("{{NAV}}", "".join(nav_html))
        .replace("{{OVERVIEW}}", "".join(cards))
        .replace("{{CHAPTERS}}", "\n".join(sections))
        .replace("{{CLOSING}}", closing)
        .replace("{{TOPIC_COUNT}}", str(topic_no))
        .replace("{{CHAPTER_COUNT}}", str(len(chapters_html)))
        .replace("{{LOGO}}", LOGO)
    )
    OUT.write_text(page, encoding="utf-8")
    SLIDES_OUT.write_text(SRC.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Wrote {OUT.name}: {len(chapters_html)} chapters, {topic_no} topics")


if __name__ == "__main__":
    main()
