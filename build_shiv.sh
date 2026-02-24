#!/bin/bash
set -e

OUTPUT="dist/wthr.pyz" 

rm -rf dist
mkdir -p dist

shiv . \
    --output-file "$OUTPUT" \
    --entry-point "wthr.main:app" \
    --python "/usr/bin/env python3"

echo "✅ Готово! Исполняемый файл находится в папке dist/"