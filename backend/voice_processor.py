import speech_recognition as sr
import logging
import threading
import time
import queue
from typing import Optional, Callable

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("VoiceProcessor")

class VoiceProcessor:
    def __init__(self):
        """Initialize voice components for backend use."""
        # Voice recognition components
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = 1.0  # Longer pauses allowed
        self.recognizer.energy_threshold = 3000  # Better for different voice volumes
        
        # Control variables
        self.is_running = False
        self.last_detected_text = "No text detected yet."
        self.voice_lock = threading.Lock()
        self.voice_queue = queue.Queue()
        self.callback = None
    
    def set_callback(self, callback: Callable[[str], None]):
        """Set a callback function to be called when text is detected."""
        self.callback = callback
    
    def voice_listener(self):
        """Voice listener thread function."""
        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                logger.info("Voice listener started")
                
                while self.is_running:
                    try:
                        logger.info("Listening for speech...")
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=7)
                        text = self.recognizer.recognize_google(audio)
                        logger.info(f"Detected speech: {text}")
                        
                        with self.voice_lock:
                            self.last_detected_text = text
                        
                        self.voice_queue.put(text)
                        
                        # Call the callback if set
                        if self.callback:
                            self.callback(text)
                            
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        logger.info("Speech not recognized")
                        continue
                    except Exception as e:
                        logger.error(f"Voice recognition error: {e}")
                        continue
        except Exception as e:
            logger.error(f"Error in voice listener: {e}")
    
    def start_listening(self):
        """Start the voice-to-text system."""
        if self.is_running:
            logger.info("Voice processor is already running")
            return False
        
        try:
            self.is_running = True
            
            # Start voice listener thread
            listener_thread = threading.Thread(target=self.voice_listener, daemon=True)
            listener_thread.start()
            
            logger.info("Voice processor started")
            return True
            
        except Exception as e:
            logger.error(f"Error starting voice processor: {e}")
            self.is_running = False
            return False
    
    def stop_listening(self):
        """Stop the voice-to-text system."""
        logger.info("Stopping voice processor...")
        self.is_running = False
        return True
    
    def get_last_detected_text(self) -> str:
        """Get the last detected text in a thread-safe manner."""
        with self.voice_lock:
            return self.last_detected_text
    
    def get_next_text(self, timeout: float = 1.0) -> Optional[str]:
        """Get the next detected text from the queue."""
        try:
            return self.voice_queue.get(timeout=timeout)
        except queue.Empty:
            return None

# For testing
if __name__ == "__main__":
    processor = VoiceProcessor()
    processor.start_listening()
    
    try:
        while True:
            text = processor.get_next_text()
            if text:
                print(f"Detected: {text}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        processor.stop_listening()
        print("Stopped")