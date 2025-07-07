import httpx
import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class ImageAndAIProcessor:
    def __init__(self):
        self.ai_model_url = os.getenv("AI_MODEL_URL", "http://localhost:12345/v1/chat/completions")
        self.rapidapi_key = os.getenv("RAPIDAPI_KEY", "")
        self.rapidapi_host = os.getenv("RAPIDAPI_HOST", "real-time-image-search.p.rapidapi.com")
    
    async def get_images(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Get image URLs from RapidAPI real-time image search."""
        try:
            async with httpx.AsyncClient() as client:
                url = "https://real-time-image-search.p.rapidapi.com/search"
                
                params = {
                    "query": query,
                    "limit": max_results,
                    "size": "any",
                    "color": "any",
                    "type": "any",
                    "time": "any",
                    "usage_rights": "any",
                    "file_type": "any",
                    "aspect_ratio": "any",
                    "safe_search": "off",
                    "region": "in"
                }
                
                headers = {
                    "x-rapidapi-host": self.rapidapi_host,
                    "x-rapidapi-key": self.rapidapi_key
                }
                
                print(f"Searching images for query: {query}")
                response = await client.get(url, params=params, headers=headers, timeout=15.0)
                
                if response.status_code != 200:
                    print(f"RapidAPI error: {response.status_code}, response: {response.text}")
                    return []
                
                data = response.json()
                print(f"RapidAPI response: {data}")
                
                images = []
                if "data" in data and isinstance(data["data"], list):
                    for item in data["data"][:max_results]:
                        image_url = item.get("url") or item.get("image")
                        source_url = item.get("source") or item.get("source_url") or image_url
                        if image_url:
                            images.append({
                                "image_url": image_url,
                                "source_url": source_url
                            })
                
                print(f"Found {len(images)} images")
                return images
                
        except Exception as e:
            print(f"Error getting images from RapidAPI: {e}")
            return []
    
    async def get_ai_response(self, prompt: str, emotion: str = "neutral") -> Dict[str, str]:
        """Get AI response for the given prompt and emotion."""
        try:
            async with httpx.AsyncClient() as client:
                try:
                    resp = await client.post(
                        self.ai_model_url,
                        json={
                            "model": "ai_teaching_assistant",
                            "messages": [{"role": "user", "content": json.dumps({"prompt": prompt, "emotion": emotion})}]
                        },
                        timeout=10.0  # Reduced timeout for faster fallback
                    )
                    
                    if resp.status_code != 200:
                        return {"result": f"AI model error: {resp.status_code}", "diagram": ""}
                    
                    data = resp.json()
                    choices = data.get("choices", [])
                    msg_content = choices[0].get("message", {}).get("content", "") if choices else ""
                    
                    try:
                        parsed = json.loads(msg_content)
                        result = parsed.get("result", "")
                        diagram = parsed.get("diagram", "")
                    except (json.JSONDecodeError, TypeError):
                        result = msg_content
                        diagram = ""
                    
                    return {"result": result, "diagram": diagram}
                    
                except httpx.ConnectError:
                    # Fallback response when AI service is not available
                    emotion_responses = {
                        "happy": "I'm glad you're feeling happy! How can I assist you today?",
                        "sad": "I'm sorry you're feeling down. Is there anything I can do to help?",
                        "angry": "I understand you might be frustrated. Let's work through this together.",
                        "fear": "It's okay to feel anxious sometimes. I'm here to help.",
                        "surprise": "That's quite surprising! Let me help you with that.",
                        "disgust": "I understand your concern. Let me try to help.",
                        "neutral": "I'm here to assist you. What would you like to know?"
                    }
                    
                    # Generate a response based on the emotion and prompt
                    response = emotion_responses.get(emotion, emotion_responses["neutral"])
                    response += f"\n\nRegarding '{prompt}', I'm currently operating in offline mode as the AI service is unavailable. I can still help with basic tasks and information."
                    
                    return {"result": response, "diagram": ""}
                
        except Exception as e:
            print(f"Error getting AI response: {e}")
            return {"result": f"I'm currently experiencing some technical difficulties, but I'm still here to help. Could you please try again or rephrase your question?", "diagram": ""}
    
    async def process_request(self, prompt: str, emotion: str = "neutral") -> Dict:
        """Process complete request: get AI response and image URLs using AI diagram."""
        try:
            # Get AI response first
            ai_response = await self.get_ai_response(prompt, emotion)
            print(f"AI response: {ai_response}")
            
            # Use only the diagram parameter from AI response as query
            diagram = ai_response.get("diagram", "").strip()
            print(f"AI diagram for image search: '{diagram}'")
            
            # Get image URLs using RapidAPI with AI diagram as query
            images = []
            if diagram:  # Only search for images if diagram is provided
                images = await self.get_images(diagram, max_results=5)
            else:
                print("No diagram provided by AI, skipping image search")
            
            return {
                "result": ai_response.get("result", ""),
                "diagram": ai_response.get("diagram", ""),
                "images": images
            }
            
        except Exception as e:
            print(f"Error processing request: {e}")
            return {
                "result": f"Error: {str(e)}",
                "diagram": "",
                "images": []
            }