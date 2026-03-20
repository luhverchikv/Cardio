#!/bin/bash
cd ~/Cardio || exit 1
source .venv/bin/activate
python -m pytest tests/ -v --tb=short
