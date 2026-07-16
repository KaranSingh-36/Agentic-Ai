from openai import OpenAI
from Config import API_KEY,BASE_URL,MODEL_NAME

if not API_KEY:
    raise RuntimeError(
        "Missing API_KEY. Set it in environment variables, Streamlit secrets, or local .env."
    )

client =OpenAI(
    api_key = API_KEY,
    base_url = BASE_URL,
)
def chat(messages: list) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        temperature=0 
    )
    
    return response.choices[0].message.content.strip()

if __name__ == "__main__":
    messages = [
        {
            "role": "user",
            "content": "say hello"
        }
    ]
    
    response = chat(messages)
    
    print(response)