# Odoo Complete Training — Website

A scrollable, responsive website built from the *Odoo Complete Training* slide deck by Cybrosys Technologies.

| File | What it is |
| --- | --- |
| `index.html` | The website: 22 chapters, 80 topics, a sidebar table of contents, and layouts that work on phones |
| `slides.html` | The original slide deck (use the arrow keys; press `F` for fullscreen), linked from the site's **Slides** button |
| `source/odoo-workflow-slides.html` | The source deck that both pages are generated from |
| `tools/build_site.py`, `tools/site_template.html` | The build script and the page layout |

## Viewing

Open `index.html` in a browser. It's a single static file, so it also works with any static host, for example GitHub Pages (Settings → Pages → deploy from branch, root folder).

## Updating the content

Edit the slides in `source/odoo-workflow-slides.html`, then rebuild:

```sh
pip install beautifulsoup4
python3 tools/build_site.py
```

This regenerates `index.html` and `slides.html`. Chapter names and the slides where each chapter starts are set in `CHAPTERS` at the top of `tools/build_site.py`. If you add or remove slides, update those start numbers.
