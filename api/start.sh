#!/bin/bash
cd /opt/render/project/src/api
exec uvicorn main:app --host 0.0.0.0 --port $PORT