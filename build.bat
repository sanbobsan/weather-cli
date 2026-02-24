@echo off
setlocal

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --clean wthr.spec

echo ✅ Готово! Исполняемый файл находится в папке dist/
pause