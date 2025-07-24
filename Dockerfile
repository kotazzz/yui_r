# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем uv, чтобы управлять зависимостями
RUN pip install uv

# Копируем pyproject.toml для установки зависимостей
# Это позволяет кэшировать этот слой, если зависимости не менялись
COPY pyproject.toml ./
RUN uv pip install --system --no-cache .

# Копируем остальной код приложения
COPY . .

# Указываем переменную окружения для вывода логов в реальном времени
ENV PYTHONUNBUFFERED=1

# Запускаем приложение
CMD ["python", "main.py"]
