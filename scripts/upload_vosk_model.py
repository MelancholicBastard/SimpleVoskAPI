from huggingface_hub import HfApi, login
from dotenv import load_dotenv
import os

REPO_ID = "MelancholicBastard/VoskModelka"
LOCAL_MODEL_FOLDER = "vosk-ru-model"

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
model_path = os.path.join(parent_dir, LOCAL_MODEL_FOLDER)
env_path = os.path.join(parent_dir, ".env")

load_dotenv(dotenv_path=env_path)
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")

print(f"Путь к модели: {model_path}")
print(f"Путь к .env: {env_path}")

if not os.path.exists(model_path):
    print(f"Папка с моделью не найдена: {model_path}")
    exit(1)

api = HfApi()

print("Авторизация...")
try:
    login(token=HF_TOKEN)
    print("Успешно!")
except Exception as e:
    print(f"Ошибка авторизации: {e}")
    exit()

try:
    api.upload_folder(
        folder_path=LOCAL_MODEL_FOLDER,
        repo_id=REPO_ID,
        repo_type="model",
        token=HF_TOKEN,
        commit_message="Upload Vosk model"
    )
    print("Загрузка завершена успешно!")
except Exception as e:
    print(f"Ошибка загрузки: {e}")