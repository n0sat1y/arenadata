#!/bin/bash

# ==========================================
# SYNOPSIS
# Объединяет все Python-файлы в проекте
# ==========================================

# Настройки
OUTPUT_FILE="all_code.txt"
# Список папок для исключения (разделенные вертикальной чертой для regex)
EXCLUDE_DIRS="venv|.venv|__pycache__|.git|.idea|env|alembic"

# Создаем выходной файл
echo "=== PYTHON CODE COLLECTION ===" > "$OUTPUT_FILE"
echo "Generated: $(date)" >> "$OUTPUT_FILE"

# Получаем список файлов
# 1. find . -name "*.py" - ищем все py файлы
# 2. grep -vE ... - исключаем пути, содержащие запрещенные папки (обрамленные слешами, чтобы не задеть похожие имена файлов)
# 3. sed 's|^\./||' - убираем "./" в начале путей для красоты
FILES=$(find . -type f -name "*.py" | grep -vE "/($EXCLUDE_DIRS)/" | sed 's|^\./||')

# Добавляем структуру
echo -e "\n=== FILE STRUCTURE ===" >> "$OUTPUT_FILE"
if [ -z "$FILES" ]; then
    echo "No Python files found." >> "$OUTPUT_FILE"
else
    echo "$FILES" >> "$OUTPUT_FILE"
fi

# Добавляем содержимое
echo -e "\n\n=== FILE CONTENTS ===" >> "$OUTPUT_FILE"

# Читаем список файлов построчно
# Использование while read гарантирует работу даже если в именах файлов есть пробелы
echo "$FILES" | while read -r file; do
    # Пропускаем пустые строки, если список пуст
    [ -z "$file" ] && continue

    echo -e "\n\n===== FILE: $file =====" >> "$OUTPUT_FILE"

    if [ -r "$file" ]; then
        cat "$file" >> "$OUTPUT_FILE"
    else
        echo "!!! COULD NOT READ FILE !!!" >> "$OUTPUT_FILE"
    fi

    echo -e "\n===== END OF FILE =====" >> "$OUTPUT_FILE"
done

echo "Done! All Python files combined in $OUTPUT_FILE"
