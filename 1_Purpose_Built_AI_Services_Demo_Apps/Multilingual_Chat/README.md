# Multilingual Chat App

A real-time multilingual chat application that demonstrates AWS Translate and Comprehend services. Three people can chat with each other in different languages (English, Spanish, French), with messages automatically translated and color-coded based on sentiment.

## Features

- **Real-time Chat**: WebSocket-based communication for instant message delivery
- **Multi-language Support**: Three chat panes for English, Spanish, and French
- **Automatic Translation**: Messages are translated to other languages in real-time
- **Sentiment Analysis**: Messages are analyzed for sentiment and color-coded:
  - **Blue**: Your own messages
  - **Green**: Positive sentiment messages from others
  - **Black**: Neutral sentiment messages from others
  - **Red**: Negative sentiment messages from others
- **Parallel Processing**: Translations run in parallel to minimize response time

## Tech Stack

### Backend
- FastAPI (Python) with WebSocket support
- boto3 (AWS SDK)
- uv (Python package manager)

### Frontend
- React + TypeScript
- Vite
- Tailwind CSS
- WebSocket client

## AWS Services Used

1. **AWS Translate** - Translates messages between English, Spanish, and French
2. **AWS Comprehend** - Analyzes sentiment of messages

## Setup

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (fast Python package installer)
- Node.js 18+
- AWS credentials with access to Translate and Comprehend services

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment using uv:
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
uv pip install -r requirements.txt
```

4. Create a `.env` file in the Multilingual_Chat directory (copy from `.env.example`):
```bash
cp .env.example .env
```

5. Edit `.env` and add your AWS credentials:
```
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

6. Start the backend server:
```bash
python main.py
```

The backend will run on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

## Usage

1. Open `http://localhost:3000` in your browser
2. You'll see three vertical chat panes:
   - **Person 1**: Types in English
   - **Person 2**: Types in Spanish
   - **Person 3**: Types in French
3. Type a message in any pane and click "Send"
4. The message will be:
   - Translated to the other two languages
   - Analyzed for sentiment
   - Displayed in all three panes with appropriate colors

## API Endpoints

### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "service": "Multilingual Chat API",
  "version": "1.0.0"
}
```

### WebSocket /ws
Real-time chat endpoint.

**Message Format (Client → Server):**
```json
{
  "sender": "person1",
  "text": "Hello!",
  "timestamp": 1234567890
}
```

**Message Format (Server → Client):**
```json
{
  "type": "message",
  "messages": {
    "person1": {
      "text": "Hello!",
      "language": "en",
      "color": "blue",
      "sender": "person1",
      "sentiment": "POSITIVE"
    },
    "person2": {
      "text": "¡Hola!",
      "language": "es",
      "color": "green",
      "sender": "person1",
      "sentiment": "POSITIVE"
    },
    "person3": {
      "text": "Bonjour!",
      "language": "fr",
      "color": "green",
      "sender": "person1",
      "sentiment": "POSITIVE"
    }
  },
  "timestamp": 1234567890
}
```

## AWS Service Calls

For each message sent:
- **2 × AWS Translate** calls (parallel) - translate to the other 2 languages
- **1 × AWS Comprehend** call - analyze sentiment

**Total: 3 API calls per message** (all run in parallel for minimal latency)

## Project Structure

```
.
├── backend/
│   ├── main.py              # FastAPI application with WebSocket
│   ├── config.py            # Configuration
│   ├── services/            # AWS service wrappers
│   │   ├── translate_service.py
│   │   └── comprehend_service.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── components/      # React components
│   │   │   └── ChatPane.tsx
│   │   ├── types.ts         # TypeScript types
│   │   └── main.tsx
│   └── package.json
└── .env.example
```

## Notes

- Messages are translated in parallel to minimize response time
- Sentiment is analyzed on the original message (sender's language)
- Color coding is applied to translated messages based on sentiment
- The sender always sees their own messages in blue
- WebSocket connection status is shown in each chat pane

## License

MIT

