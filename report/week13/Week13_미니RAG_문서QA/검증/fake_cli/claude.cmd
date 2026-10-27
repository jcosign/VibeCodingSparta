@echo off
rem fake claude CLI for verification only (no external call). Output comes from fake_claude.py
"%~dp0..\..\project\student\.venv\Scripts\python.exe" "%~dp0fake_claude.py" %*
