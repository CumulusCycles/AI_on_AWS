from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import json
import logging
import asyncio
from services.translate_service import TranslateService
from services.comprehend_service import ComprehendService
from config import (
    BACKEND_HOST,
    BACKEND_PORT,
    CORS_ORIGINS,
    LANGUAGES,
    logger
)

app = FastAPI(
    title="Multilingual Chat API",
    version="1.0.0",
    description="Real-time multilingual chat with AWS Translate and Comprehend"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
translate_service = TranslateService()
comprehend_service = ComprehendService()

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        try:
            await websocket.accept()
            self.active_connections.append(websocket)
            logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {e}", exc_info=True)
            raise
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        message_json = json.dumps(message)
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
                disconnected.append(connection)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)

manager = ConnectionManager()


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns the status of the API service.
    """
    return {
        "status": "healthy",
        "service": "Multilingual Chat API",
        "version": "1.0.0"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # Accept WebSocket connection
    # Note: WebSockets don't use CORS middleware, but we can check origin if needed
    origin = websocket.headers.get("origin", "")
    logger.info(f"WebSocket connection attempt from origin: {origin}")
    
    try:
        await manager.connect(websocket)
        logger.info("WebSocket connection established successfully")
    except Exception as e:
        logger.error(f"Failed to establish WebSocket connection: {e}", exc_info=True)
        return
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            sender = message_data.get("sender")  # person1, person2, or person3
            text = message_data.get("text", "").strip()
            
            if not text:
                continue
            
            if sender not in LANGUAGES:
                logger.warning(f"Invalid sender: {sender}")
                continue
            
            sender_language = LANGUAGES[sender]["code"]
            
            # Get target languages (all other languages)
            target_languages = [
                LANGUAGES[person]["code"]
                for person in LANGUAGES.keys()
                if person != sender
            ]
            
            logger.info(f"Processing message from {sender} ({sender_language}): {text[:50]}...")
            
            # Run translation and sentiment analysis in parallel
            translation_task = translate_service.translate_to_multiple(
                text, target_languages, sender_language
            )
            sentiment_task = comprehend_service.detect_sentiment(text, sender_language)
            
            # Wait for both to complete
            translations, sentiment = await asyncio.gather(translation_task, sentiment_task)
            
            # Build message for each person
            messages = {}
            for person, lang_info in LANGUAGES.items():
                lang_code = lang_info["code"]
                
                if person == sender:
                    # Sender sees their own message in blue
                    messages[person] = {
                        "text": text,
                        "language": lang_code,
                        "color": "blue",
                        "sender": sender,
                        "sentiment": sentiment.get("sentiment", "NEUTRAL")
                    }
                else:
                    # Others see translated message with sentiment-based color
                    translated_text = translations.get(lang_code, text)
                    sentiment_value = sentiment.get("sentiment", "NEUTRAL")
                    
                    # Determine color based on sentiment
                    if sentiment_value == "POSITIVE":
                        color = "green"
                    elif sentiment_value == "NEGATIVE":
                        color = "red"
                    else:  # NEUTRAL or MIXED
                        color = "black"
                    
                    messages[person] = {
                        "text": translated_text,
                        "language": lang_code,
                        "color": color,
                        "sender": sender,
                        "sentiment": sentiment_value
                    }
            
            # Broadcast to all connected clients
            await manager.broadcast({
                "type": "message",
                "messages": messages,
                "timestamp": message_data.get("timestamp")
            })
            
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)
    finally:
        logger.info("WebSocket endpoint cleanup")


if __name__ == "__main__":
    import uvicorn
    import asyncio
    logger.info(f"Starting server on {BACKEND_HOST}:{BACKEND_PORT}")
    uvicorn.run(app, host=BACKEND_HOST, port=BACKEND_PORT)

