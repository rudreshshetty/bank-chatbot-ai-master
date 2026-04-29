@echo off
cd /d "%~dp0"
python -m streamlit run bank_main.py --server.port 8501 --server.address 127.0.0.1
pause
