FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN apt update && apt upgrade && apt -y install curl
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uwsgi", "--http", "0:0:0:0:8000", "--master", "-p", "4", "-w", "wsgi:app"]