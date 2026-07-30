@echo off
cd /d "%~dp0"

rem PyInstaller borra toda dist\OpenTuyaSync\ antes de reconstruirla, y con
rem eso se lleva puesto config.json (dispositivos, credenciales de Spotify)
rem -- se guarda una copia aca y se restaura al final para no perderlo en
rem cada rebuild.
if exist dist\OpenTuyaSync\config.json (
  copy /y dist\OpenTuyaSync\config.json config.json.bak >nul
  echo Config existente respaldado.
)

echo Compilando OpenTuya Sync...
python -m PyInstaller --noconfirm ^
  --name OpenTuyaSync ^
  --windowed ^
  --icon assets\icon.ico ^
  --add-data "assets;assets" ^
  --collect-all dxcam ^
  --collect-all soundcard ^
  --collect-all bleak ^
  --collect-all winrt ^
  main.py

if exist config.json.bak (
  move /y config.json.bak dist\OpenTuyaSync\config.json >nul
  echo Config restaurado.
)

echo.
echo Listo. El ejecutable esta en dist\OpenTuyaSync\OpenTuyaSync.exe
pause
