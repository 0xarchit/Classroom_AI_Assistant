# AI Teaching Assistant System

This project integrates emotion detection, voice-to-text, AI processing, and text-to-voice capabilities into a web-based teaching assistant system. Powered by FastAPI and LLaMA 3.1 3B, it bridges the gap between human emotions and AI responses, creating a real-time emotion-driven interaction experience.

## Features

- **Emotion Detection**: Detects user's facial emotions in real-time using DeepFace
- **Voice-to-Text**: Converts user's speech to text for natural language input
- **AI Processing**: Processes user queries with emotion-aware AI responses
- **Image Search**: Finds relevant images based on contextual prompts
- **Text-to-Voice**: Converts AI responses to speech with emotion-appropriate voice synthesis
- **Web Interface**: Modern UI built with HTML, TailwindCSS, and JavaScript

## System Architecture

### Backend
- FastAPI server with asynchronous WebSocket implementation
- Connection management system handling multiple concurrent users
- Integration of multiple AI components
- Efficient state tracking of user emotions, interactions, and responses
- Asynchronous processing for better performance

### Frontend
- Responsive design with TailwindCSS
- Real-time WebSocket communication for seamless interactions
- Camera integration for emotion detection
- Dynamic UI updates based on emotion detection
- Speech recognition using Web Speech API

### System Flow Diagram

```mermaid
graph TD
    User[User] -->|Speaks & Shows Emotion| UI[Frontend UI]
    
    subgraph "Frontend"
        UI -->|Captures Video| EmotionCapture[Emotion Capture]
        UI -->|Records Audio| SpeechCapture[Speech Capture]
        EmotionCapture -->|Base64 Image| WebSocket
        SpeechCapture -->|Text| WebSocket[WebSocket Connection]
        WebSocket -->|Responses| UIUpdate[UI Updates]
        UIUpdate -->|Display| UI
    end
    
    WebSocket <-->|Bidirectional Communication| Server[FastAPI Server]
    
    subgraph "Backend"
        Server -->|Manages| ConnectionMgr[Connection Manager]
        Server -->|Processes Image| EmotionDetection[Emotion Detection]
        Server -->|Processes Text| AIProcessing[LLaMA 3.1 Processing]
        EmotionDetection -->|Emotion State| AIProcessing
        AIProcessing -->|Response Text| TextToSpeech[Text-to-Speech]
        AIProcessing -->|Image Prompt| ImageSearch[Image Search]
        TextToSpeech -->|Audio File| Server
        ImageSearch -->|Image URL| Server
    end
    
    Server -->|Audio & Images & Text| WebSocket
```

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- Webcam for emotion detection
- Microphone for voice input
- Internet connection for AI processing and image search

### Installation

1. Clone the repository or navigate to the project directory

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   - Rename `.env.example` to `.env` (or create a new `.env` file)
   - Add your RapidAPI key for image search
   - Configure any other environment variables as needed
   
   Example `.env` file:
   ```
   RAPIDAPI_KEY="your_rapidapi_key_here"
   RAPIDAPI_HOST="real-time-image-search.p.rapidapi.com"
   AI_MODEL_URL="http://localhost:12345/v1/chat/completions"
   ```

4. Run the server:
   ```
   python server.py
   ```

5. Open your browser and navigate to:
   ```
   http://localhost:8000
   ```

## Usage

1. Click the "Start Assistant" button to begin
2. Allow camera and microphone permissions when prompted
3. Speak clearly to interact with the assistant
4. The system will:
   - Detect your emotion
   - Convert your speech to text
   - Process your query with AI
   - Display relevant images
   - Speak the AI response

## Components

- **main.py**: FastAPI backend server
- **emotion_processor.py**: Handles facial emotion detection
- **voice_processor.py**: Manages speech-to-text conversion
- **img_and_ai.py**: Handles image search and AI processing
- **TextToVoice.py**: Manages text-to-speech conversion
- **index.html**: Main frontend interface
- **styles.css**: Custom styling
- **app.js**: Frontend JavaScript logic

## Project Structure

```
version1/
├── README.md               # Project documentation
├── requirements.txt        # Python dependencies
├── server.py               # Main server entry point
├── .env                    # Environment Variables
├── backend/
│   ├── emotion_processor.py      # Emotion detection processing
│   ├── haarcascade_frontalface_default.xml  # Face detection model
│   ├── img_and_ai.py             # Image processing utilities
│   ├── main.py                   # FastAPI application logic
│   ├── TextToVoice.py            # Text-to-speech functionality
│   └── voice_processor.py        # Speech recognition functionality
└── frontend/
    ├── static/
    │   ├── app.js                # Frontend JavaScript
    │   ├── styles.css            # CSS styling
    │   └── final_audio_*.mp3     # Generated audio responses
    └── templates/
        └── index.html            # Main web interface
```

## AI Core & Technical Details

### AI Model
- LLaMA 3.1 3B (8-bit) fine-tuned on 9,000+ emotion-labeled Q&A pairs
- Custom emotion-aware prompt engineering with context preservation
- Dedicated processing pipeline for each detected emotional state
- Local model deployment with optimized inference for responsive interactions

### Emotion Detection
- DeepFace with real-time webcam processing
- Base64 image encoding for efficient WebSocket transmission
- Continuous emotional state tracking with state management

### Voice Interaction
- Speech-to-Text for natural language input
- Edge Text-to-Speech with emotion-appropriate voice synthesis
- Unique audio file generation with UUID-based identification

### Image Search
- Contextual image sourcing driven by prompt
- Dynamic content generation that adapts to both query and detected emotion
- Integrated image processing with AI-generated responses

## Implementation Details

This isn't just an API wrapper—it's a complete system with:
- Custom WebSocket architecture handling real-time bidirectional communication
- End-to-end emotion processing pipeline from detection to response generation
- Local model deployment with optimized inference for responsive interactions
- Comprehensive error handling and logging system
- No external LLM APIs were used due to project restrictions—everything runs locally

### Emotional Intelligence Architecture
- Real-time emotion detection feeding continuously into the AI decision matrix
- Calibrated to different emotional states
- Stateful conversation tracking that maintains emotional context
- Adaptive voice characteristics matching the detected emotional state
- Connection Manager tracking user state across multiple sessions

## Resources

### Dataset and Model
- Dataset: [Ques-Ans-with-Emotion](https://huggingface.co/datasets/0xarchit/Ques-Ans-with-Emotion) - 9,000+ emotion-labeled Q&A pairs
- Model: [AI Teaching Assistant](https://huggingface.co/0xarchit/ai_teaching_assistant) - Fine-tuned LLaMA 3.1 3B

## Troubleshooting

- If the camera doesn't work, check browser permissions
- If speech recognition fails, ensure your microphone is working
- If the server fails to start, check if port 8000 is available

## License

This project is part of the Intel Unnati program, completed by team Bitbots.