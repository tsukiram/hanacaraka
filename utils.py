# C:\Users\rama\Desktop\hanacaraka\HANACARAKA\utils.py
import json
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

@lru_cache(maxsize=4)
def load_json_data(file_path):
    """Load JSON data from file with caching."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.debug(f"Loaded JSON file: {file_path}")
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading JSON file {file_path}: {str(e)}")
        raise