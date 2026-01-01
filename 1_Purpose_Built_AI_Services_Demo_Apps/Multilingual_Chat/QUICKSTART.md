# Quick Start Guide

## Prerequisites

1. Python 3.11+ installed
2. [uv](https://github.com/astral-sh/uv) installed (fast Python package installer)
3. Node.js 18+ installed
4. AWS credentials configured (access key and secret key)
5. AWS services enabled: Translate, Comprehend

## Setup Steps

### 1. Configure AWS Credentials

Create a `.env` file in the Multilingual_Chat directory:

```bash
cp .env.example .env
```

Edit `.env` and add your AWS credentials:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

**Note:** Ensure your AWS credentials have permissions to:
- `translate:TranslateText` (to translate messages)
- `comprehend:DetectSentiment` (to analyze sentiment)

### 2. Start Backend

```bash
cd backend
uv venv --python=python3.12
source .venv/bin/activate
uv pip install -r requirements.txt -q
python main.py
```

Backend will run on `http://localhost:8000`

### 3. Start Frontend (in a new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on `http://localhost:3000`

### 4. Use the App

1. Open `http://localhost:3000` in your browser
2. You'll see three vertical chat panes:
   - **Person 1**: Type messages in English
   - **Person 2**: Type messages in Spanish
   - **Person 3**: Type messages in French
3. Type a message in any pane and click "Send"
4. Watch as:
   - Your message appears in blue in your pane
   - Translated messages appear in other panes
   - Messages are color-coded by sentiment:
     - **Green**: Positive sentiment
     - **Black**: Neutral sentiment
     - **Red**: Negative sentiment

## How It Works

- Each person types in their native language
- Messages are automatically translated to the other two languages
- Sentiment analysis determines the color of translated messages
- All processing happens in parallel for minimal latency
- Real-time updates via WebSocket

## Testing Tips

Try these messages to see different sentiments:

**Positive (will show in green):**
- English: "Hello! How are you? I'm doing great!"
- Spanish: "¡Hola! ¿Cómo estás? ¡Estoy muy bien!"
- French: "Bonjour! Comment allez-vous? Je vais très bien!"

**Negative (will show in red):**
- English: "I'm not happy about this situation."
- Spanish: "No estoy contento con esta situación."
- French: "Je ne suis pas content de cette situation."

**Neutral (will show in black):**
- English: "The meeting is at 3 PM."
- Spanish: "La reunión es a las 3 PM."
- French: "La réunion est à 15h."

## Troubleshooting

### Backend won't start
- Check that Python 3.11+ is installed
- Verify `uv` is installed: `uv --version`
- Verify `.env` file exists and has correct AWS credentials
- Ensure all dependencies are installed: `uv pip install -r requirements.txt`

### Frontend won't start
- Check that Node.js 18+ is installed
- Run `npm install` to install dependencies
- Check that port 3000 is not in use

### WebSocket Connection Issues
- Make sure backend is running on port 8000
- Check browser console for WebSocket errors
- Verify CORS settings in `.env` match your frontend URL

### AWS Service Errors
- Verify AWS credentials are correct
- Check that AWS services are enabled in your AWS account
- Ensure your AWS region supports Translate and Comprehend (us-east-1 recommended)
- Verify your AWS credentials have the required permissions

### Translation Not Working
- Check AWS Translate service is enabled in your account
- Verify you have sufficient AWS Translate quota/limits
- Check backend logs for translation errors

### Sentiment Analysis Not Working
- Check AWS Comprehend service is enabled in your account
- Verify the language code is supported by Comprehend
- Check backend logs for sentiment analysis errors

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

