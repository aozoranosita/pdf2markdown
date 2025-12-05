import time
import io
import json
import logging
from pathlib import Path
import hashlib

# Doclingのコアモジュール
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    AcceleratorOptions,
    AcceleratorDevice,
    OcrMacOptions,
    TableStructureOptions, # 表設定用
    TableFormerMode        # 表の高精度モード用
)

# 要素の型判定用 (docling-core >= 2.0.0)
from docling_core.types.doc import (
    PictureItem,
    TableItem,
    SectionHeaderItem,
    TextItem,
    ListItem,
    GroupItem
)


_log = logging.getLogger(__name__)


def main(input_doc_path, output_dir):
    logging.basicConfig(level=logging.INFO)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # Docling Parse without EasyOCR
    # -------------------------
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(
        do_cell_matching=True,       # OCR結果と表セルのマッチングを行う
        mode=TableFormerMode.ACCURATE # 精度優先モード (デフォルトはFAST)
    )
    # 画像設定 (3.0x = 高解像度)
    pipeline_options.images_scale = 3.0
    pipeline_options.generate_picture_images = True 
    # アクセラレータ設定
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=4, 
        device=AcceleratorDevice.AUTO
    )

    doc_converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Docling Parse with EasyOCR (default)
    # -------------------------------
    # Enables OCR and table structure with EasyOCR, using automatic device
    # selection via AcceleratorOptions. Adjust languages as needed.
    #pipeline_options = PdfPipelineOptions()
    #pipeline_options.do_ocr = True
    #pipeline_options.do_table_structure = True
    #pipeline_options.table_structure_options.do_cell_matching = True
    #pipeline_options.ocr_options.lang = ["es"]
    #pipeline_options.accelerator_options = AcceleratorOptions(
    #    num_threads=4, device=AcceleratorDevice.AUTO
    #)

    #doc_converter = DocumentConverter(
    #    format_options={
    #        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    #    }
    #)

    # Docling Parse with EasyOCR (CPU only)
    # -------------------------------------
    # pipeline_options = PdfPipelineOptions()
    # pipeline_options.do_ocr = True
    # pipeline_options.ocr_options.use_gpu = False  # <-- set this.
    # pipeline_options.do_table_structure = True
    # pipeline_options.table_structure_options.do_cell_matching = True

    # doc_converter = DocumentConverter(
    #     format_options={
    #         InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    #     }
    # )

    # Docling Parse with Tesseract
    # ----------------------------
    # pipeline_options = PdfPipelineOptions()
    # pipeline_options.do_ocr = True
    # pipeline_options.do_table_structure = True
    # pipeline_options.table_structure_options.do_cell_matching = True
    # pipeline_options.ocr_options = TesseractOcrOptions()

    # doc_converter = DocumentConverter(
    #     format_options={
    #         InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    #     }
    # )

    # Docling Parse with Tesseract CLI
    # --------------------------------
    # pipeline_options = PdfPipelineOptions()
    # pipeline_options.do_ocr = True
    # pipeline_options.do_table_structure = True
    # pipeline_options.table_structure_options.do_cell_matching = True
    # pipeline_options.ocr_options = TesseractCliOcrOptions()

    # doc_converter = DocumentConverter(
    #     format_options={
    #         InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    #     }
    # )

    # Docling Parse with ocrmac (macOS only)
    # --------------------------------------
    # pipeline_options = PdfPipelineOptions()
    # pipeline_options.do_ocr = True
    # pipeline_options.do_table_structure = True
    # pipeline_options.table_structure_options.do_cell_matching = True
    # pipeline_options.ocr_options = OcrMacOptions()

    # doc_converter = DocumentConverter(
    #     format_options={
    #         InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    #     }
    # )

    ###########################################################################

    ## Export results
    #output_dir.mkdir(parents=True, exist_ok=True)
    #doc_filename = conv_result.input.file.stem

    # Export Markdown format:
    #with (output_dir / f"{doc_filename}.md").open("w", encoding="utf-8") as fp:
    #    fp.write(conv_result.document.export_to_markdown())

    # Export Docling document JSON format:
    #with (output_dir / f"{doc_filename}.json").open("w", encoding="utf-8") as fp:
    #    fp.write(json.dumps(conv_result.document.export_to_dict()))

    # Export Text format (plain text via Markdown export):
    #with (output_dir / f"{doc_filename}.txt").open("w", encoding="utf-8") as fp:
    #    fp.write(conv_result.document.export_to_markdown(strict_text=True))

    # Export Document Tags format:
    #with (output_dir / f"{doc_filename}.doctags").open("w", encoding="utf-8") as fp:
    #    fp.write(conv_result.document.export_to_doctags())

    print(f"処理を開始します: {input_doc_path}")
    start_time = time.time()

    try:
        # 4. 変換実行
        result = doc_converter.convert(input_doc_path)
        doc = result.document
        
        # 5. カスタムMarkdown生成ループ
        # export_to_markdown()を一括で呼ぶのではなく、要素ごとに処理して
        # 画像リンクを正しいパスで埋め込みます。
        
        md_lines = []
        image_counter = 0

        print("ドキュメント要素の書き出しを開始します...")

        # ドキュメント内の全要素を読み順（Reading Order）で走査
        for item, level in doc.iterate_items():
            
            # --- 見出し ---
            if isinstance(item, SectionHeaderItem):
                prefix = "#" * item.level
                md_lines.append(f"\n{prefix} {item.text}\n")
            
            # --- テキスト ---
            elif isinstance(item, TextItem):
                # 通常のテキスト
                md_lines.append(f"{item.text}\n")
            
            # --- リスト ---
            elif isinstance(item, ListItem):
                # リストアイテム (・など)
                marker = "-" if not item.enumerated else "1."
                md_lines.append(f"{marker} {item.text}\n")

            # --- 表 (Table) ---
            elif isinstance(item, TableItem):
                # 表としてMarkdown形式で出力
                # DoclingのTableItemはexport_to_markdownメソッドを持っています
                table_md = item.export_to_markdown()
                md_lines.append(f"\n{table_md}\n")
                print("  -> 表を出力しました")

            # --- 画像 (Picture) ---
            elif isinstance(item, PictureItem):
                
                # 画像データを取得して保存
                img = item.get_image(doc)
                if img:
                    width, height = img.size
                    if min(width, height) < 200:
                        continue
                    image_counter += 1
                    page_no = item.prov[0].page_no if item.prov else "unknown"
                    
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    hash = hashlib.sha256(buf.getvalue()).hexdigest()[:16]  # 先頭16文字
                    image_filename = f"{hash}.jpg"
                    img_path = images_dir / image_filename
                    
                    img.save(img_path, "JPEG")
                    
                    md_lines.append(f"\n![図{image_counter}](images/{image_filename})\n")
                    print(f"  -> 画像を保存・リンク: {image_filename}")

        # 6. Markdownファイルの保存
        md_content = "".join(md_lines)
        md_filename = output_dir / f"{Path(input_doc_path).stem}.md"
        
        with open(md_filename, "w", encoding="utf-8") as f:
            f.write(md_content)

        end_time = time.time()
        print(f"\n完了しました: {md_filename}")
        print(f"所要時間: {end_time - start_time:.2f}秒")
        print(f"合計画像数: {image_counter}枚")

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    data_folder = Path("/path/to/your/PDFs/directory/")
    output_dir = Path("/path/to/your/output/directory/")
    #input_doc_path = data_folder / "your_file.pdf"
    #main(input_doc_path, output_dir)
    duplicated = [f.stem for f in output_dir.glob("*.md")]
    for input_doc_path in data_folder.glob("*.pdf"):
        if input_doc_path.stem not in duplicated:
            main(input_doc_path, output_dir)

