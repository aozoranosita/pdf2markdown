# PDF to Markdown Converter

This project contains Python scripts to convert PDF files to Markdown format. The scripts use the `docling` library to perform the conversion, including options for OCR, table extraction, and image extraction.

## Scripts

- `OCR_pdf.py`: This script converts a single PDF file to Markdown. It is configured to use the macOS native OCR engine for Japanese and English text.
- `pdf2md_main.py`: This script can process multiple PDF files from a specified directory. It is configurable to use different OCR engines (or no OCR), with commented-out examples for EasyOCR, Tesseract, and ocrmac.

## Features

- Convert PDF to Markdown.
- Extract text, tables, and images.
- Support for various OCR engines through the `docling` library.
- Customizable output for images and tables.

## Dependencies

The main dependency is the `docling` library. You can install it using pip:

```bash
pip install docling
```

Depending on the OCR engine you choose, you might need to install other dependencies. For example, to use Tesseract, you will need to have the Tesseract binary installed on your system. Please refer to the `docling` documentation for more details.

## Usage

Before running the scripts, you need to modify the hardcoded paths for the input and output files/directories.

### `OCR_pdf.py`

1.  Open `OCR_pdf.py` in a text editor.
2.  Locate the `if __name__ == "__main__":` block at the end of the file.
3.  Change the `data_folder`, `output_dir`, and `pdf_file` variables to point to your input PDF and desired output directory.

```python
if __name__ == "__main__":
    # --- 設定項目 ---
    data_folder = Path("/path/to/your/PDFs/directory/")
    output_dir = Path("/path/to/your/output/directory/")
    pdf_file = data_folder / "your_file.pdf"
    convert_pdf_to_markdown_japanese(INPUT_PDF_PATH=str(pdf_file), output_dir=output_dir)
```

4.  Run the script from your terminal:

```bash
python OCR_pdf.py
```

### `pdf2md_main.py`

1.  Open `pdf2md_main.py` in a text editor.
2.  In the `if __name__ == "__main__":` block, modify the `data_folder` and `output_dir` variables.

```python
if __name__ == "__main__":
    data_folder = Path("/path/to/your/PDFs/directory/")
    output_dir = Path("/path/to/your/output/directory/")
    #input_doc_path = data_folder / "your_file.pdf"
    #main(input_doc_path, output_dir)
    duplicated = [f.stem for f in output_dir.glob("*.md")]
    for input_doc_path in data_folder.glob("*.pdf"):
        if input_doc_path.stem not in duplicated:
            main(input_doc_path, output_dir)
```

3.  This script is set up to loop through all PDF files in the `data_folder`.
4.  Run the script:

```bash
python pdf2md_main.py
```

## Configuration

The scripts can be configured by changing the `PdfPipelineOptions` in the `docling` library. You can enable/disable OCR, change the OCR engine, and adjust other settings. The `pdf2md_main.py` script contains several commented-out examples for different OCR configurations.
