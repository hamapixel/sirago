FROM python:3.12-slim
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip==26.3 'setuptools>=78.1.1' \
 && python -m pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python","manage.py","runserver","0.0.0.0:8000"]
