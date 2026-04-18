import pandas as pd

from src.detection.validation import mask_data


def generate_csv_report(results: list, output_file: str):
    report_data = []
    for res in results:
        if res.get("error"):
            report_data.append(
                {
                    "Путь": res["file_path"],
                    "Формат": res["file_type"],
                    "УЗ": "Ошибка чтения",
                    "Категории": "",
                    "Количество": 0,
                    "Пример (Маскированный)": str(res["error"]),
                }
            )
            continue

        cat_str = "; ".join(
            [f"{k}: {v['count']}" for k, v in res["categories"].items()]
        )
        total = sum(v["count"] for v in res["categories"].values())

        # Берем первый пример и маскируем его
        example_cat = list(res["categories"].keys())[0]
        example_raw = res["categories"][example_cat]["examples"][0]
        masked_example = f"{example_cat}: {mask_data(example_raw, example_cat)}"

        report_data.append(
            {
                "Путь": res["file_path"],
                "Формат": res["file_type"],
                "УЗ": res["level"],
                "Категории": cat_str,
                "Количество": total,
                "Пример (Маскированный)": masked_example,
            }
        )

    df = pd.DataFrame(report_data)
    df.to_csv(output_file, index=False, encoding="utf-8-sig")  # utf-8-sig для Excel
    print(f"\nОтчет сохранен в {output_file}")
