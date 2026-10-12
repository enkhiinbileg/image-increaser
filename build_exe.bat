@echo off
echo Packaging Webtoon Processor to EXE...
python -m PyInstaller --noconsole --onefile --name="WebtoonProcessor" main.py
echo Done! EXE file should be located in the 'dist' directory.
pause
