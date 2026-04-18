"""
Обработчики для извлечения текста из различных форматов файлов
"""

import os
import logging
from typing import Optional, List
from pathlib import Path
from abc import ABC, abstractmethod

# Обработка PDF
try:
    import PyPDF2
    import pdfplumber
except ImportError:
    PyPDF2 = None
    pdfplumber = None

# Обработка DOCX
try:
    from docx import Document
except ImportError:
    Document = None

# Обработка структурированных данных
try:
    import pandas as pd
except ImportError:
    pd = None

# Обработка HTML
try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# OCR для изображений
try:
    from PIL import Image
    from paddleocr import PaddleOCR
except ImportError:
    Image = None
    PaddleOCR = None

# Обработка видео
try:
    import cv2
except ImportError:
    cv2 = None


logger = logging.getLogger(__name__)


class FileProcessor(ABC):
    """Базовый класс для обработчиков файлов"""
    
    @abstractmethod
    def can_process(self, file_path: str) -> bool:
        """Проверка, может ли обработчик обработать файл"""
        pass
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из файла"""
        pass


class PDFProcessor(FileProcessor):
    """Обработчик PDF файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.pdf')
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из PDF с использованием нескольких библиотек"""
        text = ""
        
        # Попытка 1: pdfplumber (лучше для сложных PDF)
        if pdfplumber:
            try:
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                if text.strip():
                    return text
            except Exception as e:
                logger.debug(f"pdfplumber failed for {file_path}: {e}")
        
        # Попытка 2: PyPDF2 (запасной вариант)
        if PyPDF2 and not text.strip():
            try:
                with open(file_path, 'rb') as file:
                    reader = PyPDF2.PdfReader(file)
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
            except Exception as e:
                logger.debug(f"PyPDF2 failed for {file_path}: {e}")
        
        return text


class DOCXProcessor(FileProcessor):
    """Обработчик DOCX файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.docx', '.doc'))
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из DOCX"""
        if not Document:
            raise ImportError("python-docx not installed")
        
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            return ""


class TextProcessor(FileProcessor):
    """Обработчик текстовых файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.txt', '.md'))
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из текстовых файлов"""
        try:
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'cp1251', 'latin1', 'utf-16']:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        return file.read()
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.error(f"Error processing text file {file_path}: {e}")
            return ""


class CSVProcessor(FileProcessor):
    """Обработчик CSV файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.csv')
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из CSV"""
        if not pd:
            raise ImportError("pandas not installed")
        
        try:
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'cp1251', 'latin1']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    # Конвертируем все данные в строки и объединяем
                    text = df.astype(str).to_string(index=False)
                    return text
                except UnicodeDecodeError:
                    continue
            return ""
        except Exception as e:
            logger.error(f"Error processing CSV {file_path}: {e}")
            return ""


class JSONProcessor(FileProcessor):
    """Обработчик JSON файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.json')
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из JSON"""
        if not pd:
            raise ImportError("pandas not installed")
        
        try:
            # Пробуем разные кодировки
            for encoding in ['utf-8', 'cp1251', 'latin1']:
                try:
                    df = pd.read_json(file_path, encoding=encoding)
                    text = df.astype(str).to_string(index=False)
                    return text
                except (UnicodeDecodeError, ValueError):
                    continue
            return ""
        except Exception as e:
            logger.error(f"Error processing JSON {file_path}: {e}")
            return ""


class ParquetProcessor(FileProcessor):
    """Обработчик Parquet файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith('.parquet')
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из Parquet"""
        if not pd:
            raise ImportError("pandas not installed")
        
        try:
            df = pd.read_parquet(file_path)
            text = df.astype(str).to_string(index=False)
            return text
        except Exception as e:
            logger.error(f"Error processing Parquet {file_path}: {e}")
            return ""


class HTMLProcessor(FileProcessor):
    """Обработчик HTML файлов"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.html', '.htm'))
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из HTML"""
        if not BeautifulSoup:
            raise ImportError("beautifulsoup4 not installed")
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
                soup = BeautifulSoup(file, 'html.parser')
                # Удаляем скрипты и стили
                for script in soup(["script", "style"]):
                    script.decompose()
                text = soup.get_text(separator='\n')
                return text
        except Exception as e:
            logger.error(f"Error processing HTML {file_path}: {e}")
            return ""


class ImageProcessor(FileProcessor):
    """Обработчик изображений с OCR"""
    
    def __init__(self):
        self.ocr = None
        if PaddleOCR:
            try:
                # Инициализация PaddleOCR с поддержкой английского и русского
                # Используем 'en' для английского, PaddleOCR поддерживает многоязычность
                self.ocr = PaddleOCR(use_angle_cls=True, lang='en')
                logger.info("PaddleOCR initialized successfully with English language")
            except Exception as e:
                logger.warning(f"Failed to initialize PaddleOCR with 'en': {e}")
                try:
                    # Попытка инициализации с минимальными параметрами
                    self.ocr = PaddleOCR(lang='en')
                    logger.info("PaddleOCR initialized with minimal parameters")
                except Exception as e2:
                    logger.error(f"Failed to initialize PaddleOCR: {e2}")
                    self.ocr = None
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.tif', '.tiff', '.jpg', '.jpeg', '.png', '.gif'))
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из изображения с помощью PaddleOCR"""
        if not self.ocr:
            logger.warning("PaddleOCR not initialized, skipping image")
            return ""
        
        try:
            # PaddleOCR возвращает результаты в формате [[[bbox], (text, confidence)], ...]
            result = self.ocr.ocr(file_path, cls=True)
            
            if not result or not result[0]:
                return ""
            
            # Извлекаем текст из результатов
            text_lines = []
            for line in result[0]:
                if line and len(line) > 1:
                    text_lines.append(line[1][0])  # line[1][0] содержит распознанный текст
            
            return '\n'.join(text_lines)
        except Exception as e:
            logger.error(f"Error processing image {file_path}: {e}")
            return ""


class VideoProcessor(FileProcessor):
    """Обработчик видео файлов (извлечение кадров для OCR)"""
    
    def can_process(self, file_path: str) -> bool:
        return file_path.lower().endswith(('.mp4', '.avi', '.mov'))
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из видео (пропускаем, т.к. звука нет)"""
        # Согласно заданию, звук в видео обрабатывать не нужно
        # Можно было бы извлекать кадры и применять OCR, но это очень ресурсоемко
        logger.info(f"Skipping video file {file_path} (no audio processing required)")
        return ""


class FileProcessorFactory:
    """Фабрика для создания обработчиков файлов"""
    
    def __init__(self):
        self.processors: List[FileProcessor] = [
            PDFProcessor(),
            DOCXProcessor(),
            TextProcessor(),  # Добавлен обработчик текстовых файлов
            CSVProcessor(),
            JSONProcessor(),
            ParquetProcessor(),
            HTMLProcessor(),
            ImageProcessor(),
            VideoProcessor(),
        ]
    
    def get_processor(self, file_path: str) -> Optional[FileProcessor]:
        """Получение подходящего обработчика для файла"""
        for processor in self.processors:
            if processor.can_process(file_path):
                return processor
        return None
    
    def extract_text(self, file_path: str) -> str:
        """Извлечение текста из файла"""
        # Проверка существования файла
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return ""
        
        # Проверка размера файла
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.warning(f"Empty file: {file_path}")
            return ""
        
        # Получение обработчика
        processor = self.get_processor(file_path)
        if not processor:
            logger.warning(f"No processor found for file: {file_path}")
            return ""
        
        try:
            text = processor.extract_text(file_path)
            if not text or not text.strip():
                logger.warning(f"No text extracted from: {file_path}")
                return ""
            return text
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
