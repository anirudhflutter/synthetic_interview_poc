import os
import openai
from dotenv import load_dotenv
load_dotenv()          # <-- load .env into environment vars

# Load your API key from environment
openai.api_key = os.getenv("OPENAI_API_KEY")

personas = {
    "Anna": "You are Anna, a 20-year-old environmentally conscious consumer.",
    "Tom": "You are Tom, a 40-year-old athletic individual.",
    "Julia": "You are Julia, a 35-year-old price‑sensitive shopper.",
}

class Agent:
    def __init__(self, name, prompt):
        self.name = name
        self.prompt = prompt

    def respond(self, question, history=None):
        messages = [{"role": "system", "content": self.prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": question})
        resp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7,
        )
        return resp.choices[0].message.content

def load_agents():
    return [Agent(name, prompt) for name, prompt in personas.items()]
