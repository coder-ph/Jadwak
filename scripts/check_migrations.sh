#!/bin/bash
# scripts/check_migrations.sh
echo "Checking for missing Django migrations..."
# Execute Django command, redirect stderr to stdout for capture
python manage.py makemigrations --check --dry-run 2>&1
# Check the exit code of the last command
if [ $? -ne 0 ]; then
    echo "ERROR: Unapplied migrations detected. Please run 'python manage.py makemigrations' and commit them."
    exit 1 # Fail the hook
fi
echo "No unapplied migrations found."
exit 0 # Pass the hook
