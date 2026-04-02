import fitz  # PyMuPDF


class PDFParser:
    def __init__(self, max_chars: int = 5000):
        self.max_chars = max_chars

    def extract_content(self, pdf_path: str) -> str | None:
        print(f"📖 正在扫描论文: {pdf_path}...")
        try:
            with fitz.open(pdf_path) as doc:
                text_parts = []
                for page in doc:
                    text_parts.append(page.get_text())

            text = " ".join(text_parts).replace("\n", " ").strip()
            return text[: self.max_chars]
        except Exception as e:
            print(f"❌ PDF 读取失败: {e}")
            return None