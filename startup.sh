#!/bin/bash
gunicorn --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker app:app
