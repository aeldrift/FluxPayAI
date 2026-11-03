import os
import fastapi
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("Api Error, There's no api_key")

model = "llama-3.3-70b-versatile"
app = fastapi.FastAPI()

class UserRequest(BaseModel):
    message: str

@app.get("/")
def home():
    return {"status": "PayPal Flux AI agent is Active"}

@app.post("/api/chat/stream")
def stream_chat_agent(payload: UserRequest):
    
    system_prompt = """
    You are an advanced, strict Flux AI Agent for PayPal Customer Support. 
    Read the user's open-ended query and determine if it falls within your acceptable PayPal support documentation context.

    ALLOWED CONTEXT TOPICS:
    - Payout holds, frozen funds, release timelines.
    - Transaction disputes, chargebacks, refund status.
    - Merchant fees, currency conversion rates, international charges.
    - Basic account access issues (password reset, card linking errors).

    CRITICAL INSTRUCTIONS:
    1. If the query is within the ALLOWED CONTEXT, provide a concise answer. Start with [REPLY] followed by your answer text.
    2. If information is unavailable or unrelated (chitchat/out of scope), you must route to a live agent. Start with [TRANSFER].
    3. After your main text response, you MUST append a triple pipe separator (|||) followed by a concise 3-field Summary Matrix for the human team: Intent, Key Details, Sentiment.

    EXACT OUTPUT FORMAT EXAMPLES:
    Example 1 (Factual Reply):
    [REPLY] International payout holds typically take up to 21 days to clear unless shipping tracking information is verified in your activity log.|||Intent: Payout hold timeline query; Details: None; Sentiment: Neutral

    Example 2 (Transfer Case):
    [TRANSFER] I don't have enough information to answer that. I am connecting you safely to our Live Agent queue...|||Intent: Casual chitchat / Out of context; Details: User asked about movies; Sentiment: Distracted
    """
    
    def event_generator():
        try:
            # Call Groq with stream=True
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": payload.message}
                ],
                temperature=0.0, # To  block hallucinations
                stream=True
            )
            
            # Yield chunks
            for chunk in completion:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            yield f"[TRANSFER] Connecting you to live support due to a system blip.|||Intent: System Error; Details: {str(e)}; Sentiment: Urgent"

   
    return StreamingResponse(event_generator(), media_type="text/event-stream")
