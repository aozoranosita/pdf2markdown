from docling.document_converter import DocumentConverter
import os

source = "/Users/gr/Documents/医師国家試験/ke225pub00-公衆衛生講座2025-記入済.pdf" # document per local path or URL
source = "/Users/gr/Documents/医師国家試験/Na.pdf" # document per local path or URL
dirname = os.path.dirname(source)
basename = os.path.basename(source).split(".")[0] + ".md"
output = os.path.join(dirname, basename)

converter = DocumentConverter()

result = converter.convert(source)
markdown_content = result.document.export_to_markdown()
with open(output, "w", encoding="utf-8") as f:
    f.write(markdown_content)

