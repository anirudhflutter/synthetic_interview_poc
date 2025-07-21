import argparse
import json
from datetime import datetime
from agents import load_agents
import openai
import ollama
from typing import Literal
import re

# Shared system instructions for all agents
SYSTEM_INSTRUCTIONS = {
    "role": "system",
    "content": (
        "You are a bilingual interview engine.\n"
        "1) Detect the question language and answer it in that language.\n"
        "2) Translate the question into the other language.\n"
        "3) Translate your answer into the other language.\n"
        "4) After the first question, explicitly reference your *own previous answer* when responding.\n"
        "5) Do not reuse the exact same phrasing across agents; embrace your unique persona voice.\n\n"
        "Return JSON only with exactly these keys: question_en, question_de, answer_en, answer_de."
    )
}

def get_llm_provider(provider: Literal["openai", "ollama"]):
    """Returns the appropriate LLM call function based on provider"""
    def openai_chat(messages, **kwargs):
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                **kwargs
            )
        except openai.OpenAIError as e:
            # log & rethrow or return a fallback
            print(f"[ERROR] OpenAI API call failed: {e}")
            return {"error": str(e)}
        return resp.choices[0].message.content
    
    def ollama_chat(messages, **kwargs):
        resp = ollama.chat(
            model='llama3',
            messages=messages,
            options={
                'temperature': 0.3,
                'num_predict': 200,
                'num_ctx': 2048
            },
            format='json',
            **kwargs
        )
        return resp['message']['content']
    
    return {
        "openai": openai_chat,
        "ollama": ollama_chat
    }[provider]

def validate_response(text: str) -> dict:
    """Ensure response is complete JSON"""
    text = text.strip()
    if not text.startswith('{'):
        text = '{' + text.split('{', 1)[-1]
    if not text.endswith('}'):
        if '"answer_de":' in text:
            text += '"}'
        else:
            text += '}'
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback to extract values if JSON is malformed
        return {
            'question_en': extract_field(text, 'question_en'),
            'question_de': extract_field(text, 'question_de'),
            'answer_en': extract_field(text, 'answer_en'),
            'answer_de': extract_field(text, 'answer_de')
        }

def extract_field(text: str, field: str) -> str:
    """Fallback extraction if JSON parsing fails"""
    pattern = f'"{field}":\\s*"([^"]*)"'
    match = re.search(pattern, text)
    return match.group(1) if match else ""

def run_interview(agents, questions, provider: Literal["openai", "ollama"] = "openai"):
    results = []
    print(f'provider {provider}')
    llm_chat = get_llm_provider(provider)
    
    histories = {
        agent.name: [
            {"role": "system", "content": f"You are {agent.name}, {agent.prompt}."},
            SYSTEM_INSTRUCTIONS.copy()
        ]
        for agent in agents
    }

    for idx, q in enumerate(questions):
        ts = datetime.utcnow().isoformat()
        for agent in agents:
            history = histories[agent.name]

            # Prepare user content
            user_content = q["question"] if isinstance(q, dict) else q
            if idx > 0:
                last_assistant = next(
                    (m for m in reversed(history) if m["role"] == "assistant"), 
                    None
                )
                if last_assistant:
                    user_content = (
                        f"{user_content}\n\n"
                        "Please reference your previous answer when responding.\n\n"
                        f"Your last answer was:\n\"{last_assistant['content']}\"\n"
                    )

            history.append({"role": "user", "content": user_content})

            try:
                raw = llm_chat(history)
                payload = validate_response(raw)

                # Validate required fields
                required_keys = ['question_en', 'question_de', 'answer_en', 'answer_de']
                if not all(key in payload for key in required_keys):
                    raise ValueError(f"Missing required keys in response: {payload}")

                results.append({
                    "timestamp": ts,
                    "agent": agent.name,
                    **payload
                })

                history.append({"role": "assistant", "content": raw})

            except Exception as e:
                print(f"Error processing {agent.name}'s response: {str(e)}")
                print(f"Raw response: {raw[:200]}...")
                continue

    return results

def main():
    parser = argparse.ArgumentParser(description="Run automated interviews using either OpenAI or Ollama")
    parser.add_argument("--questions", required=True, help="Path to JSON file containing questions")
    parser.add_argument("--provider", choices=["openai", "ollama"], default="openai",
                       help="LLM provider to use (default: openai)")
    args = parser.parse_args()

    with open(args.questions) as f:
        data = json.load(f)
        questions = data["questions"] if isinstance(data, dict) else data

    agents = load_agents()
    results = run_interview(agents, questions, args.provider)
    
    output_file = f"results_{args.provider}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"Interview complete using {args.provider.upper()}. Results saved to {output_file}")

if __name__ == '__main__':
    main()