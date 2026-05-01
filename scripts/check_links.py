#!/usr/bin/env python3
"""Check that every internal href/src in _site/ resolves to an actual file
under the deployed GitHub Pages base path.

GitHub Pages serves this site at `/lean-eval-leaderboard/`, so a link like
`/foo` (root-absolute) or `../foo` (popping past the base) silently passes
a flat `linkchecker _site/` check but 404s in production. We catch this by
mounting `_site/` under that prefix and validating that every internal
URL falls inside the base path AND points at a real file.

Usage: scripts/check_links.py [--site-dir _site] [--prefix lean-eval-leaderboard]

Exits 0 with no broken links, 1 otherwise.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urlsplit, urljoin


ATTR_HOSTING_LINKS = {
    "a": "href",
    "link": "href",
    "script": "src",
    "img": "src",
    "iframe": "src",
}


class LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.base: str | None = None
        self.links: list[tuple[str, int]] = []  # (href, line)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == "base" and "href" in a and a["href"]:
            self.base = a["href"]
            return
        attr = ATTR_HOSTING_LINKS.get(tag)
        if not attr:
            return
        v = a.get(attr)
        if not v:
            return
        line = self.getpos()[0]
        self.links.append((v, line))


def extract_links(html: str) -> tuple[str | None, list[tuple[str, int]]]:
    p = LinkExtractor()
    p.feed(html)
    return p.base, p.links


def is_external(url: str) -> bool:
    s = urlsplit(url)
    return bool(s.scheme) and s.scheme not in ("", "file")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", default="_site")
    ap.add_argument("--prefix", default="lean-eval-leaderboard")
    args = ap.parse_args()

    site = pathlib.Path(args.site_dir).resolve()
    if not site.is_dir():
        print(f"site dir not found: {site}", file=sys.stderr)
        return 2

    prefix = "/" + args.prefix.strip("/") + "/"

    # Gather every HTML file in _site and the page URL it would be served at.
    pages: list[tuple[pathlib.Path, str]] = []
    for path in site.rglob("*.html"):
        rel = path.relative_to(site).as_posix()
        # Treat foo/index.html as foo/, otherwise foo/bar.html as the file.
        if rel.endswith("/index.html"):
            url_path = prefix + rel[: -len("index.html")]
        elif rel == "index.html":
            url_path = prefix
        else:
            url_path = prefix + rel
        pages.append((path, url_path))

    issues: list[str] = []
    checked = 0

    for path, url_path in pages:
        try:
            html = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            issues.append(f"{path}: read error: {e}")
            continue
        base_href, links = extract_links(html)
        # Resolve <base href> against the page URL.
        page_url = "http://example.com" + url_path
        base_url = urljoin(page_url, base_href) if base_href else page_url
        for href, line in links:
            checked += 1
            if href.startswith(("mailto:", "javascript:", "data:", "#")):
                continue
            if is_external(href):
                # http(s):// URLs to other hosts: skip — out of scope here.
                if not href.startswith("http://example.com"):
                    continue
                target = href
            else:
                target = urljoin(base_url, href)
            ts = urlsplit(target)
            if ts.netloc and ts.netloc != "example.com":
                continue
            tpath = ts.path or "/"
            # Must be inside the GitHub Pages base path.
            if not tpath.startswith(prefix):
                issues.append(
                    f"{path}:{line}: link `{href}` resolves to `{tpath}` "
                    f"which is outside the base path `{prefix}`"
                )
                continue
            # Must point at a real file/dir under _site/.
            rel = tpath[len(prefix):]
            if rel.endswith("/"):
                candidates = [site / rel / "index.html", site / rel.rstrip("/")]
            else:
                candidates = [site / rel]
                if not "." in rel.split("/")[-1]:
                    candidates.append(site / rel / "index.html")
            if not any(c.exists() for c in candidates):
                issues.append(
                    f"{path}:{line}: link `{href}` resolves to `{tpath}` "
                    f"but no file exists under {site}"
                )

    if issues:
        print(f"check_links: {len(issues)} broken link(s) in {checked} checked:", file=sys.stderr)
        for i in issues:
            print("  " + i, file=sys.stderr)
        return 1
    print(f"check_links: ok, {checked} links across {len(pages)} pages")
    return 0


if __name__ == "__main__":
    sys.exit(main())
