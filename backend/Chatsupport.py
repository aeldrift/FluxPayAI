import os
import fastapi
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("Api Error, There's no api key")

model = "llama-3.3-70b-versatile"
app = fastapi.FastAPI()

class UserRequest(BaseModel):
    message: str

PAYPAL_POLICY_KNOWLEDGE_BASE = {
    "Holds": (
        "PayPal may place a temporary hold on your funds for up to 21 days to ensure a secure transaction. "
        "Holds are common for new sellers, international cross-border sales, or sudden spikes in transaction volume. "
        "Funds can be released earlier (usually within 3-7 days) if you upload valid carrier tracking information "
        "and the buyer confirms receipt of the item."
    ),
    "Disputes": (
        "Buyers can file a dispute in the Resolution Center within 180 days of the transaction date. "
        "Disputes can be opened for 'Item Not Received' (INR) or 'Significantly Not as Described' (SNAD). "
        "Once a dispute is filed, the buyer and seller have 20 days to communicate and resolve it. "
        "If unresolved, either party can escalate the dispute to a formal claim for PayPal to investigate."
    ),
    "Fees": (
        "Standard domestic merchant processing fees are 2.99% + $0.49 per transaction. "
        "For international cross-border payments, an additional percentage-based fee of 1.50% applies, "
        "along with a fixed fee based on the currency received. Currency conversion incurs a 3.0% spread "
        "above the wholesale exchange rate."
    ),
    "Access": (
        "If your account is locked due to multiple invalid login attempts, password resets can be requested via "
        "verified email or SMS OTP. Card linking errors usually occur if the billing address matches incorrectly "
        "with your bank records or if the card is already linked to another active PayPal profile."
    )
}


@app.get("/")
def home():
    return {"status": "PayPal Flux AI agent is Active"}

@app.post("/api/chat/stream")
def stream_chat_agent(payload: UserRequest):
    
    system_prompt = """
    You are an advanced, strictly professional Flux AI Agent for PayPal Customer Support. 
    Read the user's open-ended query and determine if it falls within your acceptable PayPal support documentation context.

    ALLOWED CONTEXT TOPICS:
    - Payout holds, frozen funds, release timelines.
    - Transaction disputes, chargebacks, refund status.
    - Merchant fees, currency conversion rates, international charges.
    - Basic account access issues (password reset, card linking errors).

    For example: Where is my payment, how much time will it need to be done?
    Say: International payout holds typically take up to 21 days to clear unless shipping tracking information is verified in your activity log.

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
