#!/bin/bash
set -e

rm -rf build dist

pyinstaller --clean wthr.spec

echo "✅ Готово! Исполняемый файл находится в папке dist/"