import asyncio
import json
import logging
import os
import sys
import uuid
from typing import Dict, List, Optional

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, Response, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import the components
from backend.emotion_processor import EmotionProcessor
from backend.voice_processor import VoiceProcessor
import sys
import os

# Add parent directory to path to import modules
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from backend.TextToVoice import EdgeTextToSpeech
from backend.img_and_ai import ImageAndAIProcessor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("backend")

# Initialize FastAPI app
app = FastAPI(title="AI Assistant", description="AI Assistant with emotion detection, voice-to-text, and text-to-voice capabilities")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
TEMPLATES_DIR = os.path.join(FRONTEND_DIR, "templates")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

# Mount static files directory
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Setup Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Initialize components
emotion_processor = EmotionProcessor()
voice_processor = VoiceProcessor()
text_to_speech = EdgeTextToSpeech()
ai_processor = ImageAndAIProcessor()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_data: Dict[str, Dict] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.user_data[client_id] = {
            "emotion": "neutral",
            "last_text": "",
            "last_response": {}
        }
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.user_data:
            del self.user_data[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")

    async def send_message(self, client_id: str, message: Dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    def get_emotion(self, client_id: str) -> str:
        return self.user_data.get(client_id, {}).get("emotion", "neutral")

    def set_emotion(self, client_id: str, emotion: str):
        if client_id in self.user_data:
            self.user_data[client_id]["emotion"] = emotion

    def set_last_text(self, client_id: str, text: str):
        if client_id in self.user_data:
            self.user_data[client_id]["last_text"] = text

    def get_last_text(self, client_id: str) -> str:
        return self.user_data.get(client_id, {}).get("last_text", "")

    def set_last_response(self, client_id: str, response: Dict):
        if client_id in self.user_data:
            self.user_data[client_id]["last_response"] = response

    def get_last_response(self, client_id: str) -> Dict:
        return self.user_data.get(client_id, {}).get("last_response", {})


# Initialize connection manager
manager = ConnectionManager()

# Define routes
@app.get("/", response_class=HTMLResponse)
async def get_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# WebSocket endpoint for emotion detection
@app.websocket("/ws/emotion/{client_id}")
async def websocket_emotion(websocket: WebSocket, client_id: str):
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive data from client
            data = await websocket.receive_text()
            json_data = json.loads(data)
            
            if "image" in json_data:
                try:
                    # Process image for emotion detection
                    emotion, _ = emotion_processor.process_base64_image(json_data["image"])
                    
                    if emotion:
                        # Update user's emotion
                        manager.set_emotion(client_id, emotion)
                        
                        # Send emotion back to client
                        await manager.send_message(client_id, {"type": "emotion", "emotion": emotion})
                    
                except Exception as e:
                    logger.error(f"Error processing emotion: {e}")
                    await manager.send_message(client_id, {"type": "error", "message": str(e)})
            
            elif "text" in json_data:
                # Process text from speech recognition
                text = json_data["text"]
                manager.set_last_text(client_id, text)
                
                # Get current emotion
                emotion = manager.get_emotion(client_id)
                
                # Process request with AI and get images
                response = await ai_processor.process_request(text, emotion)
                manager.set_last_response(client_id, response)
                
                # Send AI response back to client
                await manager.send_message(client_id, {"type": "ai_response", "response": response})
                
                # Convert AI response to speech
                result_text = response.get("result", "")
                if result_text:
                    # Generate a unique filename for the audio
                    audio_filename = f"temp_audio_{uuid.uuid4()}.mp3"
                    audio_path = os.path.join(STATIC_DIR, audio_filename)
                    
                    # Save audio file
                    await text_to_speech.save_audio_async(result_text, audio_path)
                    
                    # Send audio URL back to client
                    audio_url = f"/static/{audio_filename}"
                    await manager.send_message(client_id, {"type": "audio", "url": audio_url})
            
            elif "stop" in json_data and json_data["stop"]:
                # Simply log that we received a stop message but won't process it
                logger.info(f"Received stop message from client {client_id} - no final response will be processed")
                
                # We're not processing final responses anymore, just acknowledge receipt
                await manager.send_message(client_id, {
                    "type": "stop_acknowledged",
                    "message": "Stop command received"
                })
    
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(client_id)

# API endpoint for text-to-speech
@app.post("/api/text-to-speech")
async def text_to_speech_api(request: Request):
    try:
        data = await request.json()
        text = data.get("text", "")
        voice = data.get("voice", None)
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Generate a unique filename for the audio
        audio_filename = f"temp_audio_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(STATIC_DIR, audio_filename)
        
        # Save audio file
        success = await text_to_speech.save_audio_async(text, audio_path, voice)
        
        if success:
            return JSONResponse({"url": f"/static/{audio_filename}"})
        else:
            raise HTTPException(status_code=500, detail="Failed to generate speech")
    
    except Exception as e:
        logger.error(f"Text-to-speech API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for AI processing
@app.post("/api/process")
async def process_api(request: Request):
    try:
        data = await request.json()
        prompt = data.get("prompt", "")
        emotion = data.get("emotion", "neutral")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Process request with AI and get images
        response = await ai_processor.process_request(prompt, emotion)
        
        return JSONResponse(response)
    
    except Exception as e:
        logger.error(f"Process API error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# API endpoint for final response processing (currently disabled)
@app.post("/api/final-response")
async def final_response_api(request: Request):
    # This endpoint is no longer used but kept for API compatibility
    logger.info("Final response API called but functionality is disabled")
    
    # Return a simple message that this feature is disabled
    return JSONResponse({
        "message": "Final response processing is currently disabled",
        "status": "feature_disabled"
    })

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting up the server...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down the server...")

# Run the FastAPI app with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)