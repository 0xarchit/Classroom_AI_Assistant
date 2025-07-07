import cv2
import numpy as np
import base64
import logging
from deepface import DeepFace
from typing import Dict, Tuple, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmotionProcessor")

class EmotionProcessor:
    def __init__(self):
        """Initialize the emotion processor."""
        try:
            # Load face cascade classifier
            self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            logger.info("Emotion processor initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize emotion processor: {e}")
            raise
    
    def process_base64_image(self, base64_image: str) -> Tuple[Optional[str], Optional[Dict]]:
        """Process a base64 encoded image and return the dominant emotion."""
        try:
            # Remove data URL prefix if present
            if ',' in base64_image:
                base64_image = base64_image.split(',')[1]
            
            # Decode base64 image
            img_data = base64.b64decode(base64_image)
            nparr = np.frombuffer(img_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.error("Failed to decode image")
                return None, None
            
            return self.process_frame(frame)
            
        except Exception as e:
            logger.error(f"Error processing base64 image: {e}")
            return None, None
    
    def process_frame(self, frame) -> Tuple[Optional[str], Optional[Dict]]:
        """Process a frame and return the dominant emotion."""
        try:
            # Convert frame to grayscale
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Convert grayscale frame to RGB format
            rgb_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
            
            # Detect faces in the frame
            faces = self.face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
            
            if len(faces) == 0:
                logger.info("No faces detected")
                return "neutral", None
            
            # Process the first face
            x, y, w, h = faces[0]
            
            # Extract the face ROI (Region of Interest)
            face_roi = rgb_frame[y:y + h, x:x + w]
            
            # Perform emotion analysis on the face ROI
            result = DeepFace.analyze(face_roi, actions=['emotion'], enforce_detection=False)
            
            # Determine the dominant emotion
            emotion = result[0]['dominant_emotion']
            emotion_scores = result[0]['emotion']
            
            logger.info(f"Detected emotion: {emotion}")
            
            return emotion, emotion_scores
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
            return "neutral", None

# For testing
if __name__ == "__main__":
    processor = EmotionProcessor()
    # Test with a sample image if available
    # result = processor.process_frame(cv2.imread('sample.jpg'))
    # print(f"Detected emotion: {result}")