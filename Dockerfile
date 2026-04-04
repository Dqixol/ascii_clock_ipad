FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN apt update && apt upgrade && apt -y install curl
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "'wsgi:app'"]