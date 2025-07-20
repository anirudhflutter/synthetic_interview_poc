#!/usr/bin/env python3
import json
import logging
from datetime import datetime
from agents import load_agents
from interview import run_interview

# configure logging so cron mails you its output
logging.basicConfig(level=logging.INFO, 
                    format="%(asctime)s %(levelname)s %(message)s")

BATCH_FILE   = "interview_batch.json"
RESULTS_FILE = "results.json"

def main():
    # 1) load batch questions
    with open(BATCH_FILE, "r") as f:
        batch = json.load(f)  # expect {"questions": [...]} or just a list
    questions = batch.get("questions", batch)

    # 2) run interview
    agents = load_agents()
    new_results = run_interview(agents, questions)

    # 3) append to results.json
    try:
        with open(RESULTS_FILE, "r") as f:
            all_results = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_results = []

    all_results.extend(new_results)
    with open(RESULTS_FILE, "w") as f:
        json.dump(all_results, f, indent=2)

    logging.info(f"Appended {len(new_results)} records to {RESULTS_FILE}")

    # 4) simulate webhook
    webhook_payload = {
        "timestamp": datetime.utcnow().isoformat(),
        "new_records": len(new_results),
        "total_records": len(all_results),
    }
    logging.info("WEBHOOK ▶️ " + json.dumps(webhook_payload))

if __name__ == "__main__":
    main()
