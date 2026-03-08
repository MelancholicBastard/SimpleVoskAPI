from huggingface_hub import HfApi, login
from dotenv import load_dotenv
import os

REPO_ID = "MelancholicBastard/VoskModelka"
folder_path = "./VoskRuModel"

api = HfApi()

load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise ValueError("Токен не найден! Проверьте файл .env")

print("Авторизация...")
try:
    login(token=HF_TOKEN)
    print("Успешно!")
except Exception as e:
    print(f"Ошибка авторизации: {e}")
    exit()

try:
    api.upload_folder(
        folder_path=folder_path,
        repo_id=REPO_ID,
        repo_type="model",
        token=HF_TOKEN,
        commit_message="Upload Test model"
    )
    print("Загрузка завершена успешно!")
except Exception as e:
    print(f"Ошибка загрузки: {e}")