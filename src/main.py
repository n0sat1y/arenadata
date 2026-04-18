import argparse
import os
from concurrent.futures import ProcessPoolExecutor, as_completed

from tqdm import tqdm

from src.config.config import settings
from src.core import crawler, dispatcher, parsers
from src.detection import classifier, detector
from src.reporting import report_generator


def init_worker():
    """Функция инициализации, вызывается при старте каждого дочернего процесса"""
    detector.init_nlp()
    parsers.init_ocr()


def process_single_file(file_path: str):
    file_type = os.path.splitext(file_path)[1].lower()
    aggregated_pii = {}

    try:
        # Читаем файл потоково (чанками)
        for chunk in dispatcher.get_text_chunks(file_path):
            if chunk.startswith("ERROR:"):
                return {"file_path": file_path, "file_type": file_type, "error": chunk}
            if not chunk.strip():
                continue

            chunk_pii = detector.find_pii_in_chunk(chunk)

            # Агрегируем результаты из чанков
            for cat, data in chunk_pii.items():
                if cat not in aggregated_pii:
                    aggregated_pii[cat] = {"count": 0, "examples": []}
                aggregated_pii[cat]["count"] += data["count"]
                if not aggregated_pii[cat]["examples"]:
                    aggregated_pii[cat]["examples"].extend(data["examples"])

    except Exception as e:
        return {"file_path": file_path, "file_type": file_type, "error": str(e)}

    if not aggregated_pii:
        return None  # ПДн нет

    # Классифицируем только итоговые суммы
    counts_only = {cat: data["count"] for cat, data in aggregated_pii.items()}
    level = classifier.classify_protection_level(counts_only)

    return {
        "file_path": file_path,
        "file_type": file_type,
        "level": level,
        "categories": aggregated_pii,
    }


def main(source_dir: str):
    print(f"Сканирование директории: {source_dir}")
    file_paths = list(crawler.crawl_files(source_dir))

    results = []
    if not file_paths:
        print("Файлы для анализа не найдены.")
        return

    print(
        f"Найдено файлов: {len(file_paths)}. Запуск пула процессов ({settings.MAX_WORKERS} workers)..."
    )

    # Передаем init_worker, чтобы Natasha загружалась 1 раз на ядро, а не на каждый файл!
    with ProcessPoolExecutor(
        max_workers=settings.MAX_WORKERS, initializer=init_worker
    ) as executor:
        futures = {
            executor.submit(process_single_file, path): path for path in file_paths
        }

        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Анализ файлов"
        ):
            try:
                res = future.result()
                if res:
                    results.append(res)
            except Exception as e:
                # Отлов жестких крешей, чтобы система не падала целиком
                file_path = futures[future]
                results.append(
                    {
                        "file_path": file_path,
                        "file_type": os.path.splitext(file_path)[1].lower(),
                        "error": f"CRITICAL WORKER ERROR: {e}",
                    }
                )

    if not results:
        print("Анализ завершен. Персональные данные или ошибки чтения не найдены.")
        return

    report_generator.generate_csv_report(results, "result.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Автоматизированный ИБ-Аудитор для поиска ПДн."
    )
    parser.add_argument(
        "--source-dir",
        type=str,
        default=settings.SOURCE_DIR,
        help="Путь к директории для сканирования.",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.source_dir):
        print(f"Ошибка: Директория '{args.source_dir}' не найдена.")
        exit(1)

    main(args.source_dir)
