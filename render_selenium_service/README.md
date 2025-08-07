# Render Selenium Service

A dedicated Selenium API service for the English Learning App, designed to run on Render's free tier.

## Features

- **Unified Selenium Service**: All Selenium operations in one instance
- **Concurrent Sessions**: Multiple browser sessions managed efficiently
- **Resource Management**: Automatic cleanup and memory optimization
- **RESTful API**: Easy integration with PythonAnywhere backend

## Services Included

### 1. Chatbot Service
- AI conversation via web scraping
- Context initialization for topics
- Response generation and parsing

### 2. Speech-to-Text Service  
- Voice recognition sessions
- Real-time transcription
- Multiple language support

### 3. Browser Management
- Session pooling and reuse
- Automatic cleanup of inactive sessions
- Memory and resource monitoring

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Chatbot
- `POST /api/chatbot/send-message` - Send message to AI
- `POST /api/chatbot/init-context` - Initialize topic context

### Speech-to-Text
- `POST /api/stt/start-recording` - Start STT session
- `GET /api/stt/get-result/<session_id>` - Get transcription
- `POST /api/stt/stop-recording/<session_id>` - Stop and get final result

### Service Management
- `GET /api/service/status` - Get service status
- `POST /api/service/cleanup` - Manual cleanup trigger

## Deployment on Render

1. Connect this repository to Render
2. Set build command: `chmod +x build.sh && ./build.sh`
3. Set start command: `gunicorn app:app`
4. Environment: `Python 3.11`

## Integration with PythonAnywhere

Replace Selenium calls in your PythonAnywhere backend with HTTP requests to this service.

Example:
```python
import requests

# Instead of local Selenium
response = requests.post('https://your-render-app.onrender.com/api/chatbot/send-message', 
                        json={'message': 'Hello', 'topic': 'greetings'})
ai_response = response.json()['response']
```

## Resource Management

- Maximum 3 concurrent browser sessions
- 10-minute session timeout
- Automatic cleanup of inactive sessions
- Memory usage monitoring
