# Docling allows us to explicitly select Tesseract as the OCR backend.
# We already installed Tesseract in the earlier lesson. We'll continue using it for the first comparison.

# Why not immediately switch OCR engines?

# Because we want to isolate the effect of adding document layout processing. If we change the OCR engine and layout parser simultaneously, we won't know which change caused an improvement.




# app/ingestion/docling_extractor.py

import json
import sys
from pathlib import Path

from docling.datamodel.base_models import (
    InputFormat,
    ConversionStatus,
)

from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TesseractCliOcrOptions,
)

from docling.document_converter import (
    DocumentConverter,
    PdfFormatOption,
)


def extract_document(file_path: str):

    # Step 1: Configure extraction
    options = PdfPipelineOptions(
        do_ocr=True,
        do_table_structure=True,
        ocr_options=TesseractCliOcrOptions(
            lang=["eng"]
        ),
    )

    # Step 2: Create converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=options
            )
        }
    )

    # Step 3: Process the first page
    result = converter.convert(
        file_path,
        page_range=(1, 1)
    )

    if result.status != ConversionStatus.SUCCESS:
        raise RuntimeError(
            f"Conversion status: {result.status}"
        )

    document = result.document

    # Step 4: Export readable Markdown
    markdown = document.export_to_markdown()

    # Step 5: Preserve structured representation
    structured = document.export_to_dict()

    output_dir = Path("data/outputs/docling")
    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    (output_dir / "extracted.md").write_text(
        markdown,
        encoding="utf-8"
    )

    (output_dir / "document.json").write_text(
        json.dumps(
            structured,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    return document, markdown


def verify_header(extracted_text: str):

    expected = {
        "department":
            "Missouri Department of Health and Senior Services",
        "phone":
            "573-751-6400",
        "fax":
            "573-751-6010",
        "director":
            "Peter Lyskowski",
        "designation":
            "Acting Director",
    }

    for field, value in expected.items():
        found = value in extracted_text

        print(
            f"{field}: "
            f"{'PASS' if found else 'REVIEW'}"
        )

if __name__ == "__main__":
    document, markdown = extract_document(
        sys.argv[1]
    )

    verify_header(markdown)

    print(markdown)
