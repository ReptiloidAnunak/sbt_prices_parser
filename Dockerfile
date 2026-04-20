FROM python:3.11-slim

WORKDIR /app
RUN python3 -m venv .venv


COPY entrypoint.sh .
RUN chmod +x ./entrypoint.sh

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .