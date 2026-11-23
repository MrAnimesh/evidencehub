
import json
import sys
from pathlib import Path

import pymupdf


def inspect_pdf(file_path: str) -> dict:
    result = {
        "filename": Path(file_path).name,
        "pages": []
    }

    with pymupdf.open(file_path) as pdf:
        result["page_count"] = len(pdf)

        for page_no, page in enumerate(pdf, start=1):
            extracted = page.get_text("dict", sort=False)

            blocks = []

            for block in extracted["blocks"]:
                bbox = [round(v, 2) for v in block["bbox"]]

                if block["type"] == 0:
                    lines = []

                    for line in block.get("lines", []):
                        text = "".join(
                            span["text"]
                            for span in line["spans"]
                        )
                        lines.append(text)

                    content = "\n".join(lines).strip()

                    if content:
                        blocks.append({
                            "type": "text",
                            "bbox": bbox,
                            "content": content
                        })

                elif block["type"] == 1:
                    blocks.append({
                        "type": "image",
                        "bbox": bbox
                    })

            text_blocks = [
                b for b in blocks
                if b["type"] == "text"
            ]

            image_blocks = [
                b for b in blocks
                if b["type"] == "image"
            ]

            text_chars = sum(
                len(b["content"]) for b in text_blocks
            )

            result["pages"].append({
                "page": page_no,
                "width": round(page.rect.width, 2),
                "height": round(page.rect.height, 2),
                "text_characters": text_chars,
                "text_block_count": len(text_blocks),
                "image_block_count": len(image_blocks),
                "needs_visual_review": text_chars < 30,
                "blocks": blocks
            })

    return result


if __name__ == "__main__":
    input_file = sys.argv[1]

    result = inspect_pdf(input_file)

    output_path = Path("data/outputs/inspection.json")
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    for page in result["pages"]:
        print(
            f"Page {page['page']}: "
            f"{page['text_characters']} characters, "
            f"{page['image_block_count']} image blocks, "
            f"visual review={page['needs_visual_review']}"
        )

