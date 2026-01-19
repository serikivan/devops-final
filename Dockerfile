# Используем официальный Python-образ
FROM python:3.11-slim

# Установка рабочей директории
WORKDIR /appCL

# Копирование зависимостей и исходников
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запуск сервера Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]