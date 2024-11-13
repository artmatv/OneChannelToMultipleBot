import json
import os

from config import DATA_FILE, ADDITIONAL_CHANNEL_IDS


def load_user_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    else:
        # Инициализируем пустую структуру данных
        return {channel_id: [] for channel_id in ADDITIONAL_CHANNEL_IDS}

def save_user_data(user_data):
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f)