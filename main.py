import logging.config
import os

# Ensure the logs directory exists
os.makedirs('logs', exist_ok=True)

# Set up structured logging
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'logs/ai_usage.log',
            'formatter': 'default',
        },
    },
    'loggers': {
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

logging.config.dictConfig(logging_config)

from fastapi import FastAPI
from routes import generate

app = FastAPI()

# Include the generate-text route
app.include_router(generate.router)

# Example usage
# Run the FastAPI server with: uvicorn main:app --reload 