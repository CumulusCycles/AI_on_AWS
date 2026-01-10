import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv('.env.local')
load_dotenv('.env')

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(
        "index:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )