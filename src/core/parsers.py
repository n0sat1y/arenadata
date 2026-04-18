import io
import json
import os
import uuid
import wave

import docx
import fitz
import pandas as pd
import pytesseract
from bs4 import BeautifulSoup
from moviepy import VideoFileClip
from PIL import Image
from striprtf.striprtf import rtf_to_text


def parse_txt(file_path: str):
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        while chunk := f.read(50000):
            yield chunk


def parse_docx(file_path: str):
    doc = docx.Document(file_path)
    text = []
    for para in doc.paragraphs:
        text.append(para.text)
        if len(text) > 500:
            yield "\n".join(text)
            text = []
    if text:
        yield "\n".join(text)


def parse_pdf(file_path: str):
    doc = fitz.open(file_path)
    for page in doc:
        text = page.get_text()
        if len(text.strip()) < 50:  # Эвристика: если текста нет, пробуем OCR
            pix = page.get_pixmap(dpi=150)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang="rus+eng")
        yield text


def parse_csv(file_path: str):
    # Читаем чанками, чтобы не убить оперативку
    for chunk in pd.read_csv(
        file_path,
        chunksize=10000,
        on_error="skip",
        sep=None,
        engine="python",
        dtype=str,
    ):
        yield chunk.to_string(index=False, header=False)


def parse_parquet(file_path: str):
    import pyarrow.parquet as pq

    parquet_file = pq.ParquetFile(file_path)
    for batch in parquet_file.iter_batches(batch_size=10000):
        yield batch.to_pandas().to_string(index=False, header=False)


def parse_excel(file_path: str):
    # Excel тяжело читать чанками, читаем по листам
    dfs = pd.read_excel(file_path, sheet_name=None, dtype=str)
    for _, df in dfs.items():
        yield df.to_string(index=False, header=False)


def parse_video_stt(file_path: str):
    import vosk

    from src.config.config import settings

    temp_audio = f"temp_{uuid.uuid4().hex}.wav"  # Безопасно для многопроцессорности
    try:
        video = VideoFileClip(file_path)
        video.audio.write_audiofile(
            temp_audio, codec="pcm_s16le", fps=16000, logger=None
        )

        model = vosk.Model(settings.VOSK_MODEL_PATH)
        rec = vosk.KaldiRecognizer(model, 16000)

        with wave.open(temp_audio, "rb") as wf:
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                if rec.AcceptWaveform(data):
                    yield json.loads(rec.Result())["text"]
            yield json.loads(rec.FinalResult())["text"]
    finally:
        if os.path.exists(temp_audio):
            os.remove(temp_audio)
