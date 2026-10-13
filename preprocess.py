#!/usr/bin/env python3
"""
Preprocess MathJax-rendered HTML for clean pandoc conversion.

Strips MathJax visual rendering spans and replaces them with raw <math>
elements so pandoc converts them to proper LaTeX math in markdown output.

Usage:
    uv run preprocess.py <input.html> <output.html>
"""

import html
import sys
from bs4 import BeautifulSoup


def preprocess(input_path: str, output_path: str) -> None:
    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "lxml")

    # Collect IDs of display-mode equations (wrapped in MathJax_Display span)
    display_ids: set[str] = set()
    for wrapper in soup.find_all("span", class_="MathJax_Display"):
        for inner in wrapper.find_all("span", class_="MathJax"):
            eid = inner.get("id")
            if eid:
                display_ids.add(eid)

    replaced = 0
    for span in soup.find_all("span", class_="MathJax"):
        mathml_escaped = span.get("data-mathml", "")
        if not mathml_escaped:
            span.decompose()
            continue

        mathml = html.unescape(mathml_escaped)

        # Mark as display math if needed
        if span.get("id", "") in display_ids:
            mathml = mathml.replace("<math ", '<math display="block" ', 1)
            mathml = mathml.replace("<math>", '<math display="block">', 1)

        math_soup = BeautifulSoup(mathml, "lxml-xml")
        span.replace_with(math_soup)
        replaced += 1

    # Remove hidden preview spans
    for span in soup.find_all("span", class_="MathJax_Preview"):
        span.decompose()

    # Remove raw MathML script tags (already inlined above)
    for script in soup.find_all("script", type="math/mml"):
        script.decompose()

    # Unwrap MathJax_Display containers (keep inner content)
    for wrapper in soup.find_all("span", class_="MathJax_Display"):
        wrapper.unwrap()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"Replaced {replaced} MathJax equations -> {output_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.html> <output.html>")
        sys.exit(1)
    preprocess(sys.argv[1], sys.argv[2])
