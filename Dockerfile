FROM python:3.14-alpine

WORKDIR /app

RUN apk add --no-cache .build-deps gcc musl-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "wsgi:app"]