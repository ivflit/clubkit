#!/bin/bash
cd /Users/ivan/GitHub/Multi-tenant-platform/backend
source venv/bin/activate
python manage.py test 2>&1
