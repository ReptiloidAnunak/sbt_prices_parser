FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

COPY . /app

RUN chmod +x run.sh

RUN python -m pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install

CMD ["bash", "run.sh"]