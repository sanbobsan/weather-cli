#!/bin/bash

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
  echo "Окружение .venv создано"
fi

. .venv/bin/activate
pip install -r requirements-dev.txt

echo "Готово! Активируйте окружение командой: \nsource .venv/bin/activate"
