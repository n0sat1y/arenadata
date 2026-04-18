#!/usr/bin/env python3
"""
Главный модуль для запуска детектора персональных данных
Использование: python main.py --dataset <путь_к_датасету> [опции]
"""

import os
import sys
import logging
import argparse
import yaml
from pathlib import Path

from src.scanner import PIIScanner


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Настройка логирования"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )


def load_config(config_path: str = "config.yaml") -> dict:
    """Загрузка конфигурации из YAML файла"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logging.warning(f"Config file {config_path} not found, using defaults")
        return {}
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}


def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='Детектор персональных данных в файловых хранилищах',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python main.py --dataset ./dataset
  python main.py --dataset ./dataset --output results.csv
  python main.py --dataset ./dataset --workers 8 --detailed
        """
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        required=True,
        help='Путь к директории с датасетом'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='pii_report.csv',
        help='Путь к выходному CSV файлу (по умолчанию: pii_report.csv)'
    )
    
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Создать детальный отчет с полной информацией о ПДн'
    )
    
    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Количество потоков для обработки (по умолчанию: 4)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Путь к файлу конфигурации (по умолчанию: config.yaml)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Уровень логирования (по умолчанию: INFO)'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        help='Путь к файлу логов (опционально)'
    )
    
    return parser.parse_args()


def main():
    """Главная функция"""
    # Парсинг аргументов
    args = parse_arguments()
    
    # Загрузка конфигурации
    config = load_config(args.config)
    
    # Настройка логирования
    log_level = args.log_level or config.get('logging', {}).get('level', 'INFO')
    log_file = args.log_file or config.get('logging', {}).get('file')
    setup_logging(log_level, log_file)
    
    logger = logging.getLogger(__name__)
    
    # Проверка существования датасета
    dataset_path = args.dataset
    if not os.path.exists(dataset_path):
        logger.error(f"Dataset directory not found: {dataset_path}")
        sys.exit(1)
    
    if not os.path.isdir(dataset_path):
        logger.error(f"Path is not a directory: {dataset_path}")
        sys.exit(1)
    
    logger.info("=" * 80)
    logger.info("Детектор персональных данных")
    logger.info("=" * 80)
    logger.info(f"Датасет: {dataset_path}")
    logger.info(f"Выходной файл: {args.output}")
    logger.info(f"Количество потоков: {args.workers}")
    logger.info("=" * 80)
    
    # Создание сканера
    scanner = PIIScanner(max_workers=args.workers)
    
    # Сканирование директории
    logger.info("Начало сканирования...")
    results = scanner.scan_directory(dataset_path)
    
    # Вывод статистики
    logger.info("=" * 80)
    logger.info(f"Сканирование завершено!")
    logger.info(f"Всего файлов с ПДн: {len(results)}")
    
    if results:
        # Статистика по уровням защищенности
        uz_stats = {}
        for result in results:
            uz = result['protection_level']
            uz_stats[uz] = uz_stats.get(uz, 0) + 1
        
        logger.info("Распределение по уровням защищенности:")
        for uz, count in sorted(uz_stats.items()):
            logger.info(f"  {uz}: {count} файлов")
        
        # Генерация отчета
        logger.info("=" * 80)
        logger.info("Генерация отчета...")
        
        # Основной отчет в формате size,time,name
        scanner.generate_csv_report(results, args.output)
        logger.info(f"Отчет сохранен: {args.output}")
        
        # Детальный отчет (опционально)
        if args.detailed:
            detailed_output = args.output.replace('.csv', '_detailed.csv')
            scanner.generate_detailed_report(results, detailed_output)
            logger.info(f"Детальный отчет сохранен: {detailed_output}")
        
        logger.info("=" * 80)
        logger.info("Готово!")
    else:
        logger.warning("Персональные данные не обнаружены ни в одном файле")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
