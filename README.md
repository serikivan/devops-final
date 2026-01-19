# Канальный уровень 
### Репозиторий для АРЭ ПО на основе проекта канального уровня в рамках курсовой работы по дисципине
### [Сетевые технологии (Networking)](https://github.com/iu5git/Networking/tree/main)
### Серик Иван РТ5-71
## Инструкция по развёртыванию

### 1. Клонирование репозитория: 
```bash
git clone https://github.com/serikivan/devops-final
cd devops-final
```

### 2. Развёртывание контейнера:

#### С помощью Docker Compose (рекомендуется):
```bash
docker compose up --build
```

#### Или в фоновом режиме:
```bash
docker compose up -d --build
```

#### Остановка контейнера:
```bash
docker compose down
```

### 3. Сборка и запуск Docker образа вручную:

#### Сборка образа:
```bash
docker build -t channel-service:latest .
```

#### Запуск контейнера:
```bash
docker run -d \
  --name channel_service \
  -p 5000:5000 \
  -e TEST_MODE=true \
  -e DEBUG=False \
  channel-service:latest
```

#### Просмотр логов:
```bash
docker logs -f channel_service
```

#### Остановка и удаление:
```bash
docker stop channel_service
docker rm channel_service
```

## Тестовый режим (без транспортного уровня)
Проект **запускается в тестовом режиме по умолчанию**.
В этом режиме внешние HTTP-отправки на транспортный уровень заменяются заглушками:
в лог выводится сообщение об отправке, а проверка подключения не выполняется.

### Запуск локально (PowerShell)
```powershell
python manage.py runserver 0.0.0.0:5000
```

### Запуск в Docker
```powershell
docker compose up --build
```

### Как отключить тестовый режим
```powershell
$env:TEST_MODE="false"
python manage.py runserver 0.0.0.0:5000
```