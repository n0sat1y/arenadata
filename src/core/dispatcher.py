import os
from . import parsers

PARSER_MAP = {
    # Структурированные форматы
    '.csv': parsers.parse_csv, 
    '.parquet': parsers.parse_parquet,
    '.json': parsers.parse_json,
    
    # Документы и текст
    '.txt': parsers.parse_txt, 
    '.xlsx': parsers.parse_excel, 
    '.xls': parsers.parse_excel,
    '.docx': parsers.parse_docx,
    '.doc': parsers.parse_doc_legacy, # <- Подключили кастомный парсер для старого .doc
    '.rtf': parsers.parse_rtf,        # <- Подключили RTF
    '.pdf': parsers.parse_pdf,
    
    # Веб
    '.html': parsers.parse_html,      # <- Подключили HTML
    '.htm': parsers.parse_html,
    
    # Изображения (через PaddleOCR)
    '.jpg': parsers.parse_image,
    '.jpeg': parsers.parse_image,
    '.png': parsers.parse_image,
    '.tif': parsers.parse_image,
    '.tiff': parsers.parse_image,
    '.gif': parsers.parse_image,      # <- Добавили GIF
    
    # Видео
    '.mp4': parsers.parse_video_stt,
}

def get_text_chunks(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    parser_func = PARSER_MAP.get(ext)
    if parser_func:
        try:
            yield from parser_func(file_path)
        except Exception as e:
            yield f"ERROR: {str(e)}"
    else:
        # Для неизвестных форматов можно попытаться прочитать их как текст
        yield f"ERROR: Unsupported extension {ext}"
