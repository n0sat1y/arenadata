"""
Утилиты для работы с детектором ПДн
"""

import os
import json
from typing import Dict, List
from datetime import datetime


def create_sample_dataset(output_dir: str = "sample_dataset"):
    """
    Создание примера датасета для тестирования
    
    Args:
        output_dir: Директория для сохранения примеров
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Пример 1: Текстовый файл с ПДн
    sample1 = """
    АНКЕТА СОТРУДНИКА
    
    ФИО: Петров Петр Петрович
    Дата рождения: 25.05.1990
    Телефон: +7 (916) 555-12-34
    Email: petrov.petr@company.ru
    
    Паспортные данные:
    Серия: 45 67
    Номер: 890123
    
    СНИЛС: 123-456-789-01
    ИНН: 771234567890
    
    Адрес регистрации:
    г. Москва, ул. Пушкина, д. 15, кв. 42
    """
    
    with open(os.path.join(output_dir, "employee.txt"), "w", encoding="utf-8") as f:
        f.write(sample1)
    
    # Пример 2: CSV с клиентами
    sample2 = """name,phone,email,inn
Иванов Иван Иванович,+79161234567,ivanov@mail.ru,123456789012
Сидорова Мария Александровна,+79267654321,sidorova@gmail.com,987654321098
Козлов Дмитрий Сергеевич,+79031112233,kozlov@yandex.ru,456789123456
"""
    
    with open(os.path.join(output_dir, "clients.csv"), "w", encoding="utf-8") as f:
        f.write(sample2)
    
    # Пример 3: JSON с данными
    sample3 = {
        "users": [
            {
                "name": "Смирнов Алексей Викторович",
                "phone": "+7 (495) 123-45-67",
                "email": "smirnov@example.com",
                "passport": "4567 123456",
                "snils": "123-456-789-01"
            },
            {
                "name": "Новикова Елена Игоревна",
                "phone": "+7 (812) 987-65-43",
                "email": "novikova@example.com",
                "passport": "6789 654321",
                "snils": "987-654-321-09"
            }
        ]
    }
    
    with open(os.path.join(output_dir, "users.json"), "w", encoding="utf-8") as f:
        json.dump(sample3, f, ensure_ascii=False, indent=2)
    
    print(f"Примеры датасета созданы в директории: {output_dir}")
    print(f"Создано файлов: 3")


def analyze_report(report_file: str):
    """
    Анализ сгенерированного отчета
    
    Args:
        report_file: Путь к CSV отчету
    """
    import csv
    
    if not os.path.exists(report_file):
        print(f"Файл отчета не найден: {report_file}")
        return
    
    with open(report_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print("=" * 80)
    print(f"Анализ отчета: {report_file}")
    print("=" * 80)
    print(f"\nВсего файлов с ПДн: {len(rows)}")
    
    # Статистика по размерам
    if rows:
        sizes = [int(row['size']) for row in rows]
        total_size = sum(sizes)
        avg_size = total_size / len(sizes)
        
        print(f"\nСтатистика по размерам:")
        print(f"  Общий размер: {total_size:,} байт ({total_size / 1024 / 1024:.2f} МБ)")
        print(f"  Средний размер: {avg_size:,.0f} байт ({avg_size / 1024:.2f} КБ)")
        print(f"  Минимальный: {min(sizes):,} байт")
        print(f"  Максимальный: {max(sizes):,} байт")
        
        # Топ-10 самых больших файлов
        print(f"\nТоп-10 самых больших файлов:")
        sorted_rows = sorted(rows, key=lambda x: int(x['size']), reverse=True)[:10]
        for i, row in enumerate(sorted_rows, 1):
            size_mb = int(row['size']) / 1024 / 1024
            print(f"  {i}. {row['name']} - {size_mb:.2f} МБ")


def compare_reports(report1: str, report2: str):
    """
    Сравнение двух отчетов
    
    Args:
        report1: Путь к первому отчету
        report2: Путь к второму отчету
    """
    import csv
    
    def read_report(path):
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return {row['name']: row for row in reader}
    
    try:
        data1 = read_report(report1)
        data2 = read_report(report2)
        
        print("=" * 80)
        print("Сравнение отчетов")
        print("=" * 80)
        
        only_in_1 = set(data1.keys()) - set(data2.keys())
        only_in_2 = set(data2.keys()) - set(data1.keys())
        common = set(data1.keys()) & set(data2.keys())
        
        print(f"\nОтчет 1: {report1}")
        print(f"  Файлов: {len(data1)}")
        
        print(f"\nОтчет 2: {report2}")
        print(f"  Файлов: {len(data2)}")
        
        print(f"\nОбщих файлов: {len(common)}")
        print(f"Только в отчете 1: {len(only_in_1)}")
        print(f"Только в отчете 2: {len(only_in_2)}")
        
        if only_in_1:
            print(f"\nФайлы только в отчете 1 (первые 10):")
            for name in list(only_in_1)[:10]:
                print(f"  - {name}")
        
        if only_in_2:
            print(f"\nФайлы только в отчете 2 (первые 10):")
            for name in list(only_in_2)[:10]:
                print(f"  - {name}")
                
    except Exception as e:
        print(f"Ошибка при сравнении отчетов: {e}")


def generate_statistics(detailed_report: str):
    """
    Генерация статистики по детальному отчету
    
    Args:
        detailed_report: Путь к детальному отчету
    """
    import csv
    from collections import Counter
    
    if not os.path.exists(detailed_report):
        print(f"Файл отчета не найден: {detailed_report}")
        return
    
    with open(detailed_report, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print("=" * 80)
    print("Статистика по персональным данным")
    print("=" * 80)
    
    # Статистика по уровням защищенности
    uz_counter = Counter(row['УЗ'] for row in rows)
    print("\nРаспределение по уровням защищенности:")
    for uz, count in sorted(uz_counter.items()):
        percentage = count / len(rows) * 100
        print(f"  {uz}: {count} файлов ({percentage:.1f}%)")
    
    # Статистика по форматам
    format_counter = Counter(row['формат_файла'] for row in rows)
    print("\nРаспределение по форматам файлов:")
    for fmt, count in format_counter.most_common():
        percentage = count / len(rows) * 100
        print(f"  {fmt}: {count} файлов ({percentage:.1f}%)")
    
    # Статистика по категориям ПДн
    all_categories = []
    for row in rows:
        categories = row['категории_ПДн'].split(', ')
        all_categories.extend(categories)
    
    category_counter = Counter(all_categories)
    print("\nНаиболее часто встречающиеся категории ПДн:")
    for category, count in category_counter.most_common(10):
        print(f"  {category}: {count} файлов")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python utils.py create_sample    - Создать примеры датасета")
        print("  python utils.py analyze <report> - Анализировать отчет")
        print("  python utils.py stats <detailed> - Статистика по детальному отчету")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "create_sample":
        create_sample_dataset()
    elif command == "analyze" and len(sys.argv) > 2:
        analyze_report(sys.argv[2])
    elif command == "stats" and len(sys.argv) > 2:
        generate_statistics(sys.argv[2])
    else:
        print("Неизвестная команда или недостаточно аргументов")
