import os
import sys
from huggingface_hub import snapshot_download

REPO_ID = "MelancholicBastard/VoskModelka"
LOCAL_MODEL_FOLDER = "vosk-ru-model"

def check_and_download_model() -> str:

    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    model_path = os.path.join(parent_dir, LOCAL_MODEL_FOLDER)

    if os.path.exists(model_path) and os.listdir(model_path):
        print(f"Модель найдена локально: {model_path}")
        return model_path
    
    print(f"Модель не найдена. Начинаем загрузку из {REPO_ID}...")

    try:
        downloaded_path = snapshot_download(
            repo_id=REPO_ID,
            repo_type="model",
            local_dir=model_path,          
            force_download=False, # Не создает символические ссылки
        )
        
        print(f"Загрузка завершена! Путь: {downloaded_path}")
        return downloaded_path

    except Exception as e:
        print(f"\n Ошибка при загрузке: {e}")
        sys.exit(1)

check_and_download_model()