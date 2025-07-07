import asyncio
import edge_tts
import pygame
import os
import logging
from typing import List, Dict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EdgeTTS")

class EdgeTextToSpeech:
    def __init__(self):
        """Initialize Microsoft Edge TTS."""
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.current_voice = "en-US-AriaNeural"
            logger.info("Edge TTS engine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pygame mixer: {e}")

    async def speak_async(self, text: str, voice: str = None):
        """Convert text to speech using Edge TTS (async)."""
        try:
            voice_to_use = voice or self.current_voice
            logger.info(f"Speaking with {voice_to_use}: {text}")
            
            # Create TTS communication
            communicate = edge_tts.Communicate(text, voice_to_use)
            
            # Save to temporary file in current directory
            temp_filename = f"temp_edge_audio_{hash(text) % 10000}.mp3"
            await communicate.save(temp_filename)
            
            # Play the audio file
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                await asyncio.sleep(0.1)
            
            # Clean up temporary file
            try:
                os.remove(temp_filename)
            except:
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Error in Edge TTS: {e}")
            return False

    def speak(self, text: str, voice: str = None):
        """Synchronous wrapper for speak_async."""
        return asyncio.run(self.speak_async(text, voice))

    async def save_audio_async(self, text: str, filename: str, voice: str = None):
        """Save text-to-speech audio to a file (async)."""
        try:
            voice_to_use = voice or self.current_voice
            
            # Ensure filename has .mp3 extension
            if not filename.endswith('.mp3'):
                filename += '.mp3'
            
            # Create TTS communication and save
            communicate = edge_tts.Communicate(text, voice_to_use)
            await communicate.save(filename)
            
            logger.info(f"Audio saved to: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return False

    def save_audio(self, text: str, filename: str, voice: str = None):
        """Synchronous wrapper for save_audio_async."""
        return asyncio.run(self.save_audio_async(text, filename, voice))

    async def get_available_voices(self) -> List[Dict]:
        """Get list of available voices."""
        try:
            voices = await edge_tts.list_voices()
            return voices
        except Exception as e:
            logger.error(f"Error getting voices: {e}")
            return []

    def list_voices(self):
        """List available voices (synchronous)."""
        voices = asyncio.run(self.get_available_voices())
        
        print("\nAvailable voices:")
        print("-" * 50)
        
        # Group by language
        lang_groups = {}
        for voice in voices:
            lang = voice['Locale']
            if lang not in lang_groups:
                lang_groups[lang] = []
            lang_groups[lang].append(voice)
        
        # Show popular languages first
        priority_langs = ['en-US', 'en-GB', 'en-AU', 'es-ES', 'fr-FR', 'de-DE', 'it-IT', 'ja-JP']
        
        for lang in priority_langs:
            if lang in lang_groups:
                print(f"\n{lang}:")
                for voice in lang_groups[lang][:3]:  # Show first 3 voices per language
                    gender = voice.get('Gender', 'Unknown')
                    print(f"  {voice['ShortName']} - {voice['FriendlyName']} ({gender})")
        
        print(f"\n... and {len(voices)} total voices available")
        return voices

    def run_interactive_mode(self):
        """Run interactive Edge TTS mode."""
        print("\n=== Microsoft Edge Text-to-Speech ===")
        print("Commands:")
        print("  Type text to speak it")
        print("  'voice <name>' - Change voice (e.g., 'voice en-US-JennyNeural')")
        print("  'voices' - List available voices")
        print("  'save <filename>' - Save last text to file")
        print("  'current' - Show current voice")
        print("  'quit' - Exit program")
        print("=" * 38)
        
        last_text = ""
        
        while True:
            try:
                user_input = input(f"\n[{self.current_voice}] Enter text: ").strip()
                
                if not user_input:
                    continue
                    
                if user_input.lower() == 'quit':
                    print("Goodbye!")
                    break
                elif user_input.lower() == 'voices':
                    self.list_voices()
                elif user_input.lower() == 'current':
                    print(f"Current voice: {self.current_voice}")
                elif user_input.lower().startswith('voice '):
                    new_voice = user_input[6:].strip()
                    if new_voice:
                        self.current_voice = new_voice
                        print(f"Voice changed to: {new_voice}")
                        # Test the new voice
                        self.speak("Voice changed successfully", new_voice)
                    else:
                        print("Please specify a voice name")
                elif user_input.lower().startswith('save '):
                    filename = user_input[5:].strip()
                    if last_text and filename:
                        self.save_audio(last_text, filename)
                    else:
                        print("No text to save or filename not provided")
                else:
                    # Speak the entered text
                    last_text = user_input
                    self.speak(user_input)
                    
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                logger.error(f"Error in interactive mode: {e}")

if __name__ == "__main__":
    # Install required packages first
    print("Make sure to install required packages:")
    print("pip install edge-tts pygame")
    print()
    
    # Create Edge TTS instance
    tts = EdgeTextToSpeech()
    
    # Test basic functionality
    tts.speak("Hello! Microsoft Edge text to speech is working perfectly.")
    
    # Run interactive mode
    tts.run_interactive_mode()