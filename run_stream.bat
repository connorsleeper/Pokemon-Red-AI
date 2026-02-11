@echo off
echo ACTIVATING ANACONDA ENVIRONMENT...
call C:\Users\NotAlive\AppData\Local\miniconda3\Scripts\activate.bat

echo STARTING POKEMON AI BROADCAST...
python gui_stream.py
pause