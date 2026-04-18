import os

from src.core import parsers

PARSER_MAP = {
    ".txt": parsers.parse_txt,
    ".csv": parsers.parse_csv,
    ".parquet": parsers.parse_parquet,
    ".xlsx": parsers.parse_excel,
    ".xls": parsers.parse_excel,
    ".doc": parsers.parse_docx,  # Заглушка, для старых doc нужен textract
    ".docx": parsers.parse_docx,
    ".pdf": parsers.parse_pdf,
    ".mp4": parsers.parse_video_stt,
}


def get_text_chunks(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    parser_func = PARSER_MAP.get(ext)
    if parser_func:
        try:
            yield from parser_func(file_path)
        except Exception as e:
            yield f"ERROR: {str(e)}"
