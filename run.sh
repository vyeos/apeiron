#!/bin/bash

echo "--- SYSTEM 1 ACTIVATED (WAKE PHASE) ---"
poetry run python core/wake_phase.py

echo ""
echo "--- INITIATING SYSTEM 2 (SLEEP PHASE) ---"
poetry run python core/sleep_phase.py

echo "--- CYCLE COMPLETE ---"
