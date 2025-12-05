import time
import io, hashlib
from pathlib import Path

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


def convert_pdf_to_markdown_japanese(INPUT_PDF_PATH, output_dir):
    # 1. 出力ディレクトリの準備
    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    # 2. パイプラインオプションの設定
    pipeline_options = PdfPipelineOptions()
    
    # OCR設定 (Mac Native)
    pipeline_options.do_ocr = True
    pipeline_options.ocr_options = OcrMacOptions(lang=["ja-JP", "en-US"]) # 日本語+英語
    
    # 画像設定 (3.0x = 高解像度)
    pipeline_options.images_scale = 3.0
    pipeline_options.generate_picture_images = True 

    # 表設定 (ここが重要: 高精度モードを指定)
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(
        do_cell_matching=True,       # OCR結果と表セルのマッチングを行う
        mode=TableFormerMode.ACCURATE # 精度優先モード (デフォルトはFAST)
    )

    # アクセラレータ設定
    pipeline_options.accelerator_options = AcceleratorOptions(
        num_threads=8, 
        device=AcceleratorDevice.AUTO
    )

    # 3. コンバーターの初期化
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    print(f"処理を開始します: {INPUT_PDF_PATH}")
    print("エンジン: Mac Native OCR (Apple Vision)")
    print("モード: 表認識(Accurate), 画像リンク生成あり")
    start_time = time.time()

    try:
        # 4. 変換実行
        result = converter.convert(INPUT_PDF_PATH)
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
                    if min(width, height) < 300:
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
        md_filename = output_dir / f"{Path(INPUT_PDF_PATH).stem}.md"
        
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
    # --- 設定項目 ---
    data_folder = Path("/path/to/your/PDFs/directory/")
    output_dir = Path("/path/to/your/output/directory/")
    pdf_file = data_folder / "your_file.pdf"
    convert_pdf_to_markdown_japanese(INPUT_PDF_PATH=str(pdf_file), output_dir=output_dir)

    # data_folder内のPDFファイルをループ
    #pdf_files = list(Path(data_folder).glob("*.pdf"))
    #for pdf_file in pdf_files[2:]:
    #    convert_pdf_to_markdown_japanese(INPUT_PDF_PATH=str(pdf_file), output_dir=output_dir)
