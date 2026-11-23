
import json
import sys
from pathlib import Path

import pymupdf


def extract_blocks(page, textpage=None):
    blocks = page.get_text(
        "blocks",
        textpage=textpage,
        sort=True
    )

    results = []

    for block in blocks:
        # block[6] identifies the block type
        # 0 means text
        if block[6] != 0:
            continue

        content = block[4].strip()

        if not content:
            continue

        results.append({
            "text": content,
            "bbox": [
                round(float(v), 2)
                for v in block[:4]
            ]
        })

    return results


def extract_pdf(file_path: str) -> dict:
    result = {
        "document": Path(file_path).name,
        "pages": []
    }

    with pymupdf.open(file_path) as pdf:
        for page_number, page in enumerate(
            pdf, start=1
        ):
            native_text = page.get_text(
                "text", sort=True
            )

            readable_chars = sum(
                ch.isalnum()
                for ch in native_text
            )

            # Simple learning heuristic:
            # not a reliable production classifier.
            needs_ocr = readable_chars < 30

            if needs_ocr:
                ocr_page = page.get_textpage_ocr(
                    language="eng",
                    dpi=300,
                    full=True
                )

                blocks = extract_blocks(
                    page,
                    textpage=ocr_page
                )

                strategy = "full_page_ocr"

            else:
                blocks = extract_blocks(page)
                strategy = "native"

            text = "\n".join(
                block["text"] for block in blocks
            )

            flags = []

            if needs_ocr:
                flags.append("low_native_text")

            if len(text.strip()) < 30:
                flags.append("little_extracted_text")

            result["pages"].append({
                "page_number": page_number,
                "strategy": strategy,
                "native_readable_chars": readable_chars,
                "extracted_text": text,
                "blocks": blocks,
                "quality_flags": flags
            })

    return result


if __name__ == "__main__":
    source = sys.argv[1]

    result = extract_pdf(source)

    output = Path(
        "data/outputs/extracted_document.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    for page in result["pages"]:
        print(
            f"Page {page['page_number']}: "
            f"{page['strategy']}, "
            f"{len(page['extracted_text'])} characters"
        )
