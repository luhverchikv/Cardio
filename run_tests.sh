#!/bin/bash

# Скрипт для запуска тестов с телефона
# Использование: bash ~/Cardio/run_tests.sh

cd ~/Cardio || exit 1

# Цвета для вывода (если терминал поддерживает)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "🧪 Запуск тестов Cardio"
echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"
echo ""

# Активация виртуального окружения
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Виртуальное окружение активировано"
else
    echo "❌ Виртуальное окружение не найдено"
    exit 1
fi

echo ""
echo "📊 Запуск тестов..."
echo "========================================"
echo ""

# Запуск тестов с сохранением результата
python -m pytest tests/ -v --tb=short 2>&1 | tee /tmp/test_results.txt

# Получение итогового статуса
RESULT=${PIPESTATUS[0]}

echo ""
echo "========================================"

if [ $RESULT -eq 0 ]; then
    echo -e "${GREEN}✅ ВСЕ ТЕСТЫ ПРОШЛИ${NC}"
else
    echo -e "${RED}❌ ТЕСТЫ ПРОВАЛИЛИСЬ${NC}"
fi

# Краткая статистика
echo ""
echo "📈 Статистика:"
grep -E "passed|failed|error|skipped" /tmp/test_results.txt | tail -1

# Если есть ошибки - показать их
if [ $RESULT -ne 0 ]; then
    echo ""
    echo "❌ Ошибки:"
    grep -A 3 "FAILED" /tmp/test_results.txt | head -20
fi

echo "========================================"
echo "⏱  Выполнено за: $(date '+%H:%M:%S')"

# Деактивация
deactivate 2>/dev/null

exit $RESULT

