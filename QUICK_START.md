# Quick Start Guide

## 🚀 How to Run the App

### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Choose Your Mode

#### Production Mode (Recommended)
```bash
START_BACKEND.bat
```
- All browser automation hidden
- Best performance
- Clean interface

#### Debug Mode (For Testing)
```bash
START_BACKEND_DEBUG_STT.bat
```
- Browser windows visible
- See SpeechTexter in action
- Visual debugging

#### Simple Mode (No Automation)
```bash
START_BACKEND_SIMPLE.bat
```
- No browser automation
- Text-only responses
- Fastest startup

### 3. Access the App
Open your browser to: http://localhost:5000

## 🎤 Voice Features

- **Unlimited voice input** via SpeechTexter
- **AI conversations** with automated browser
- **70+ languages** supported
- **No API limits** or costs

## 🛠️ Utilities

- `TEST_BACKEND_CONNECTION.bat` - Test server connectivity
- `VIEW_DATABASE_WEB.bat` - View database in browser

## 📁 Project Structure

```
englishlearningapp/
├── backend/          # Flask server & AI services
├── frontend/         # HTML/CSS/JS interface
├── data/            # Database & user data
└── venv/            # Python virtual environment
```

## ⚠️ Troubleshooting

1. **Virtual environment issues**: Delete `venv` folder and reinstall
2. **Browser not opening**: Use `START_BACKEND_DEBUG_STT.bat` to see browsers
3. **Voice not working**: Check microphone permissions in browser
4. **Port conflicts**: Make sure port 5000 is available

For detailed setup instructions, see `DEPLOYMENT_CHECKLIST.md`.
