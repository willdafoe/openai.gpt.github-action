import os
import logging
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Load environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")  # Ensure correct API base URL

# Initialize OpenAI client (NEW API)
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)

# Function to retry OpenAI requests on rate limits
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def get_chatgpt_fix(error_message):
    logging.info("Requesting fix from OpenAI...")

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI that fixes code errors efficiently."},
                {"role": "user", "content": f"Fix this error:\n{error_message}"}
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        logging.error(f"❌ OpenAI API Error: {e}")
        return None
