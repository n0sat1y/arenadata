import os
import uuid
import json
import pandas as pd
import fitz
import docx
import json
import wave
import numpy as np
from moviepy import VideoFileClip
from striprtf.striprtf import rtf_to_text
from bs4 import BeautifulSoup
import logging

# Глобальная переменная для воркера
ocr_model = None

def parse_html(file_path: str):
    """Парсинг HTML с удалением тегов и скриптов"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
        # Удаляем невидимые элементы (скрипты, стили)
        for script in soup(["script", "style"]):
            script.extract()
            
        text = soup.get_text(separator='\n', strip=True)
        # Отдаем текст чанками, чтобы не перегрузить NLP
        for i in range(0, len(text), 50000):
            yield text[i:i+50000]

def parse_rtf(file_path: str):
    """Извлечение текста из RTF-документов"""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        try:
            text = rtf_to_text(f.read())
            for i in range(0, len(text), 50000):
                yield text[i:i+50000]
        except Exception:
            yield "ERROR: RTF parsing failed"

def parse_json(file_path: str):
    """
    Умный парсинг JSON. 
    В корпоративных дампах JSON часто бывает в формате JSON Lines (построчный).
    Мы пытаемся прочитать его чанками. Если не выходит (это единый массив) — читаем стандартно.
    """
    try:
        # Пробуем как JSONL (JSON Lines) батчами
        for chunk in pd.read_json(file_path, lines=True, chunksize=10000, dtype=str):
            yield chunk.to_string(index=False, header=False)
    except ValueError:
        # Если это обычный JSON, загружаем целиком, но отдаем чанками
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            data = json.load(f)
            text = json.dumps(data, ensure_ascii=False)
            for i in range(0, len(text), 50000):
                yield text[i:i+50000]

def parse_doc_legacy(file_path: str):
    """
    Эвристический парсер старого бинарного .doc.
    Поскольку мы не можем использовать системные пакеты типа antiword (может не быть на сервере жюри),
    мы читаем бинарник и вытаскиваем из него все читаемые кириллические и латинские символы.
    Для поиска ПДн (ФИО, цифры, паспорта) этого более чем достаточно!
    """
    import re
    with open(file_path, 'rb') as f:
        content = f.read().decode('cp1251', errors='ignore') # .doc обычно в 1251
        # Оставляем только буквы, цифры, пробелы и базовую пунктуацию
        text = re.sub(r'[^\w\s\-\.,@]', ' ', content)
        # Убираем множественные пробелы (сжимаем мусор)
        text = re.sub(r'\s+', ' ', text)
        for i in range(0, len(text), 50000):
            yield text[i:i+50000]

def init_ocr():
    """Инициализация PaddleOCR один раз для процесса (воркера)"""
    global ocr_model
    if ocr_model is None:
        from paddleocr import PaddleOCR
        # Отключаем дебаг-спам от PaddleOCR в консоль
        logging.getLogger('ppocr').setLevel(logging.ERROR)
        # use_angle_cls=True - автоматически переворачивает кривые сканы
        ocr_model = PaddleOCR(use_angle_cls=True, lang='ru', show_log=False)

def extract_paddle_text(result) -> str:
    """Хелпер для извлечения текста из вывода PaddleOCR"""
    if not result or not result[0]:
        return ""
    return "\n".join([line[1][0] for line in result[0]])

def parse_txt(file_path: str):
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        while chunk := f.read(50000): yield chunk

def parse_docx(file_path: str):
    doc = docx.Document(file_path)
    text =[]
    for para in doc.paragraphs:
        text.append(para.text)
        if len(text) > 500:
            yield "\n".join(text)
            text =[]
    if text: yield "\n".join(text)

def parse_pdf(file_path: str):
    init_ocr() # Гарантируем, что модель загружена
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 50: 
            # Эвристика: текста нет, значит это скан. Включаем OCR.
            # alpha=False гарантирует 3 канала (RGB) без прозрачности
            pix = page.get_pixmap(dpi=150, alpha=False)
            
            # Конвертируем Pixmap напрямую в numpy-массив без сохранения на диск!
            img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
            
            result = ocr_model.ocr(img_array, cls=True)
            yield extract_paddle_text(result)
        else:
            yield text

def parse_image(file_path: str):
    """Обработка отдельно лежащих картинок (jpg, png, tiff)"""
    init_ocr()
    # PaddleOCR умеет сам читать пути к файлам
    result = ocr_model.ocr(file_path, cls=True)
    yield extract_paddle_text(result)

def parse_csv(file_path: str):
    for chunk in pd.read_csv(file_path, chunksize=10000, on_error='skip', sep=None, engine='python', dtype=str):
        yield chunk.to_string(index=False, header=False)

def parse_parquet(file_path: str):
    import pyarrow.parquet as pq
    parquet_file = pq.ParquetFile(file_path)
    for batch in parquet_file.iter_batches(batch_size=10000):
        yield batch.to_pandas().to_string(index=False, header=False)

def parse_excel(file_path: str):
    dfs = pd.read_excel(file_path, sheet_name=None, dtype=str)
    for _, df in dfs.items():
        yield df.to_string(index=False, header=False)

def parse_video_stt(file_path: str):
    import vosk
    from config import settings
    temp_audio = f"temp_{uuid.uuid4().hex}.wav"
    try:
        video = VideoFileClip(file_path)
        video.audio.write_audiofile(temp_audio, codec='pcm_s16le', fps=16000, logger=None)
        
        model = vosk.Model(settings.VOSK_MODEL_PATH)
        rec = vosk.KaldiRecognizer(model, 16000)
        
        with wave.open(temp_audio, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0: break
                if rec.AcceptWaveform(data): 
                    yield json.loads(rec.Result())['text']
            yield json.loads(rec.FinalResult())['text']
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
