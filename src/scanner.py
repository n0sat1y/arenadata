"""
Основной модуль для сканирования файлов и обнаружения персональных данных
"""

import os
import logging
import csv
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from src.file_processors import FileProcessorFactory
from src.pii_detector import PIIDetector
from src.classifier import ProtectionLevelClassifier, ProtectionLevel


logger = logging.getLogger(__name__)


class PIIScanner:
    """Сканер файлов для обнаружения персональных данных"""
    
    def __init__(self, max_workers: int = 4):
        self.processor_factory = FileProcessorFactory()
        self.pii_detector = PIIDetector()
        self.classifier = ProtectionLevelClassifier()
        self.max_workers = max_workers
    
    def scan_directory(self, directory: str) -> List[Dict]:
        """
        Рекурсивное сканирование директории
        
        Args:
            directory: Путь к директории для сканирования
            
        Returns:
            Список результатов сканирования
        """
        # Получение списка всех файлов
        all_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                all_files.append(file_path)
        
        logger.info(f"Found {len(all_files)} files to process")
        
        # Многопоточная обработка файлов
        results = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Создаем задачи
            future_to_file = {
                executor.submit(self.process_file, file_path): file_path 
                for file_path in all_files
            }
            
            # Обработка результатов с прогресс-баром
            with tqdm(total=len(all_files), desc="Processing files") as pbar:
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                    except Exception as e:
                        logger.error(f"Error processing {file_path}: {e}")
                    finally:
                        pbar.update(1)
        
        return results
    
    def process_file(self, file_path: str) -> Dict:
        """
        Обработка одного файла
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Словарь с результатами анализа или None если ПДн не найдены
        """
        try:
            # Извлечение текста
            text = self.processor_factory.extract_text(file_path)
            if not text:
                return None
            
            # Обнаружение ПДн
            pii_results = self.pii_detector.detect(text)
            if not pii_results:
                return None
            
            # Подсчет находок
            pii_counts = self.pii_detector.count_by_category(pii_results)
            
            # Классификация уровня защищенности
            protection_level = self.classifier.classify(pii_counts)
            
            # Получение метаданных файла
            file_stat = os.stat(file_path)
            file_size = file_stat.st_size
            file_mtime = datetime.fromtimestamp(file_stat.st_mtime)
            file_name = os.path.basename(file_path)
            
            return {
                'path': file_path,
                'name': file_name,
                'size': file_size,
                'mtime': file_mtime,
                'pii_categories': list(pii_counts.keys()),
                'pii_counts': pii_counts,
                'protection_level': protection_level.value,
                'format': Path(file_path).suffix
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return None
    
    def generate_csv_report(self, results: List[Dict], output_file: str):
        """
        Генерация CSV отчета в формате: size,time,name
        
        Args:
            results: Список результатов сканирования
            output_file: Путь к выходному файлу
        """
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                
                # Заголовок
                writer.writerow(['size', 'time', 'name'])
                
                # Данные
                for result in results:
                    # Форматирование времени как в примере: "sep 26 18:31"
                    time_str = result['mtime'].strftime('%b %d %H:%M').lower()
                    
                    writer.writerow([
                        result['size'],
                        time_str,
                        result['name']
                    ])
            
            logger.info(f"CSV report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating CSV report: {e}")
            raise
    
    def generate_detailed_report(self, results: List[Dict], output_file: str):
        """
        Генерация детального отчета с полной информацией
        
        Args:
            results: Список результатов сканирования
            output_file: Путь к выходному файлу
        """
        try:
            with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'путь', 'имя_файла', 'размер', 'время_изменения',
                    'категории_ПДн', 'количество_находок', 'УЗ', 'формат_файла'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                
                for result in results:
                    categories_str = ', '.join(result['pii_categories'])
                    counts_str = ', '.join(
                        f"{cat}:{count}" 
                        for cat, count in result['pii_counts'].items()
                    )
                    
                    writer.writerow({
                        'путь': result['path'],
                        'имя_файла': result['name'],
                        'размер': result['size'],
                        'время_изменения': result['mtime'].strftime('%Y-%m-%d %H:%M:%S'),
                        'категории_ПДн': categories_str,
                        'количество_находок': counts_str,
                        'УЗ': result['protection_level'],
                        'формат_файла': result['format']
                    })
            
            logger.info(f"Detailed report saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Error generating detailed report: {e}")
            raise
