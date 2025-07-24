# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt || pip install --no-cache-dir -r pyproject.toml

# Указываем переменную окружения для запуска в контейнере
ENV PYTHONUNBUFFERED=1

# Запускаем приложение
CMD ["python", "main.py"]
