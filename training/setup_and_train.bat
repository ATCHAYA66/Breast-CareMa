@echo off
setlocal
cd /d "%~dp0\.."
if not exist .venv (py -3.11 -m venv .venv)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r training\requirements-training.txt
if not exist datasets\BUSI\Dataset_BUSI_with_GT echo Extract archive.zip into datasets\BUSI\Dataset_BUSI_with_GT, then run this file again. & pause & exit /b 1
python training\prepare_busi.py --data datasets\BUSI
python training\train_classifier.py --pretrained
python training\train_segmenter.py
pause
