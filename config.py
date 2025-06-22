#config.py

import os
from groq import Groq

class Config:
    GROQ_API_KEY = "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"
    # GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    client = Groq(api_key=GROQ_API_KEY)