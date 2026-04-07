@echo off
echo === STAR Regional Intelligence System - Data Pipeline ===
cd /d %~dp0
echo Step 1: Generating synthetic data...
python data/synthetic/generate_data.py
echo.
echo Step 2: Running analysis pipeline...
python -m backend.pipeline.run_pipeline
echo.
echo Pipeline complete. Start backend next.
pause
