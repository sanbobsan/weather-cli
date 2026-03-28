
VENV = .venv
ifeq ($(OS), Windows_NT)
    VENV_BIN = $(VENV)/Scripts
    PYTHON = $(VENV_BIN)/python.exe
    PIP = $(VENV_BIN)/pip.exe
	PYINSTALLER = $(VENV_BIN)/pyinstaller.exe
    SHIV = $(VENV_BIN)/shiv.exe
else
    VENV_BIN = $(VENV)/bin
    PYTHON = $(VENV_BIN)/python
    PIP = $(VENV_BIN)/pip
	PYINSTALLER = $(VENV_BIN)/pyinstaller
    SHIV = $(VENV_BIN)/shiv
endif

.PHONY: help setup setup-dev build build-exe build-shiv build-dist upload check test typecheck run clean
.DEFAULT_GOAL := help

help:
	@echo "Команды для подготовки:"
	@echo "  setup          - Создать venv и установить основные зависимости"
	@echo "  setup-dev      - Установить зависимости для разработки (тесты, линтеры)"
	@echo ""
	@echo "Проверка и тесты:"
	@echo "  check          - Запустить тесты и проверку типов"
	@echo "  test           - Запустить тесты"
	@echo "  typecheck      - Запустить проверку типов"
	@echo ""
	@echo "Команды сборки (в папку dist/):"
	@echo "  build          - Запустить обе сборки (EXE и SHIV)"
	@echo "  build-exe      - Собрать бинарный файл через PyInstaller"
	@echo "  build-shiv     - Собрать самораспаковывающийся архив .pyz через Shiv"
	@echo ""
	@echo "Работа с приложением:"
	@echo "  run            - Запустить локально через venv. Пример: make run ARGS=\"--help\""
	@echo "  clean          - Удалить venv, папку dist, build и кэш python"

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-build.txt
	$(PIP) install -e .

setup-dev: setup
	$(PIP) install -r requirements-dev.txt

build: build-exe build-shiv

build-exe:
	rm -rf build dist/wthr
	$(PYINSTALLER) --clean wthr.spec
	@echo "✅ Готово! Исполняемый файл находится в папке dist/"

build-shiv:
	@rm -f dist/wthr.pyz
	@mkdir -p dist
	$(SHIV) . \
	    --output-file dist/wthr.pyz \
	    --entry-point "wthr.main:app" \
	    --python "/usr/bin/env python3"
	@echo "✅ Готово! Архив .pyz находится в папке dist/"

build-dist:
	rm -rf dist/*.whl dist/*.tar.gz
	$(PYTHON) -m pip install --upgrade build
	$(PYTHON) -m build

upload: build-dist
	$(PYTHON) -m pip install --upgrade twine
	$(PYTHON) -m twine upload dist/*.whl dist/*.tar.gz --verbose

check: test typecheck

test:
	$(PYTHON) -m pytest

typecheck:
	$(PYTHON) -m mypy src tests

run:
	$(PYTHON) -m wthr.main $(ARGS)

clean:
	rm -rf $(VENV) build dist
	find . -type d -name "__pycache__" -exec rm -rf {} +