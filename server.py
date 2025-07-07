import os
import sys
import uvicorn
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
sys.path.append(str(SERVER_DIR))

from backend.main import app

def main():
    """Run the FastAPI server."""
    print("Starting AI Assistant server...")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()