import os
import json

DATA_FILE = 'user_data.json'
BOT_TOKEN = os.getenv('BOT_TOKEN')
MAIN_FORUM_ID = os.getenv('MAIN_CHANNEL_ID')
LOGS_CHANNEL_ID = os.getenv('LOGS_CHANNEL_ID')
ADDITIONAL_CHANNEL_IDS = json.loads(os.getenv('CHANNELS_ARRAY_IDS'))
