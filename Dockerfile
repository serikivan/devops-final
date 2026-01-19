# Используем официальный Python-образ
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Создаём непривилегированного пользователя для безопасности
RUN useradd -m -u 1000 appuser && \
    mkdir -p /appCL && \
    chown -R appuser:appuser /appCL

# Установка рабочей директории
WORKDIR /appCL

# Копирование зависимостей (для оптимизации кэша Docker)
COPY --chown=appuser:appuser requirements.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY --chown=appuser:appuser . .

# Переключаемся на непривилегированного пользователя
USER appuser

# Собираем статические файлы Django (если используются)
# RUN python manage.py collectstatic --noinput || true

# Проверка работоспособности Django
RUN python manage.py check --deploy || true

# Открываем порт
EXPOSE 5000

# Healthcheck для мониторинга контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/swagger/').read()" || exit 1

# Запуск сервера Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:5000"]