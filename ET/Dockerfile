FROM python:3.14-slim

WORKDIR /apps

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  hx curl htop
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

ARG APPS_PATH="worktrees/python/amber-chasm/python/apps"

COPY ET/requirements.txt .
COPY ${APPS_PATH}/main.py ./main.py
COPY $APPS_PATH/extract/ ./extract/
COPY $APPS_PATH/transform/ ./transform/
COPY $APPS_PATH/logger.py ./logger.py
COPY $APPS_PATH/processed ./processed
COPY $APPS_PATH/incoming ./incoming
COPY $APPS_PATH/failed ./failed
COPY $APPS_PATH/done ./done
COPY $APPS_PATH/document.py ./document.py
COPY $APPS_PATH/ready ./ready
COPY $APPS_PATH/sent_json ./sent_json

RUN pip install -r requirements.txt

EXPOSE 5000

ENV PYTHONUNBUFFERED=1

# CMD ["sleep infinity"]





