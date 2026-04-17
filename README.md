# DockerWithVosk

## Описание проекта
DockerWithVosk — это проект, предоставляющий API для распознавания речи с использованием библиотеки [Vosk](https://alphacephei.com/vosk/). API позволяет обрабатывать аудиофайлы и получать текстовую расшифровку.

## Зависимости
Для работы проекта необходимы следующие зависимости:

- **Python** >= 3.14
- **FastAPI** (>=0.135.1, <0.136.0) — веб-фреймворк для создания API.
- **Vosk** (>=0.3.45, <0.4.0) — библиотека для распознавания речи.
- **Uvicorn** [standard] (>=0.41.0, <0.42.0) — ASGI-сервер для запуска FastAPI.
- **python-multipart** (>=0.0.20, <0.1.0) — для обработки multipart-запросов.
- **python-dotenv** (>=1.2.2, <2.0.0) — для работы с переменными окружения.
- **huggingface-hub** (>=1.7.1, <2.0.0) — для интеграции с Hugging Face.

Все зависимости указаны в файле `pyproject.toml` и могут быть установлены с помощью Poetry.

## Структура проекта
- **src/**: Исходный код проекта.
  - `main.py`: Основной файл для запуска API.
  - `decode.py`: Логика обработки аудиофайлов.
- **scripts/**: Скрипты для работы с моделями Vosk.
  - `download_vosk_model.py`: Скрипт для загрузки модели.
  - `upload_vosk_model.py`: Скрипт для загрузки модели в облако.
- **vosk-ru-model/**: Папка с моделью Vosk для русского языка.

## Запуск проекта

1. Клонируйте репозиторий с GitHub:
   ```bash
   git clone https://github.com/MelancholicBastard/SimpleVoskAPI.git
   cd SimpleVoskAPI
   ```

2. Убедитесь, что у вас установлен Python версии 3.14 или выше.
3. Установите Poetry для управления зависимостями:
   ```bash
   pip install poetry
   ```

4. Установите зависимости проекта:
   ```bash
   poetry install
   ```

5. Запустите приложение (рекомендуется через `uvicorn`):

   Запуск в одной команде через Poetry:
   ```bash
   poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
   ```

После запуска API будет доступно по адресу: [http://localhost:8000](http://localhost:8000).

Пример запроса к эндпоинту `/health`:

```bash
curl http://localhost:8000/health
# Ответ (пример):
#{"status":"ok","model_path":"vosk-ru-model","recognizer_pool_size":4,"chunk_size":4000}
```
