@echo off
cd /d "%~dp0"
echo Compilando OpenTuya Sync...
python -m PyInstaller --noconfirm ^
  --name OpenTuyaSync ^
  --windowed ^
  --icon assets\icon.ico ^
  --add-data "assets;assets" ^
  --collect-all dxcam ^
  --collect-all soundcard ^
  main.py
echo.
echo Listo. El ejecutable esta en dist\OpenTuyaSync\OpenTuyaSync.exe
pause
