from flask import Flask, request, jsonify
from agents import load_agents
from interview import run_interview
import json

import os
from supabase import create_client, Client
from pyairtable.exceptions import InvalidParameterError
from pyairtable import Table
from config import validate_env
validate_env()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
AIRTABLE_TOKEN     = os.getenv("AIRTABLE_TOKEN")
AIRTABLE_BASE_ID   = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE     = os.getenv("AIRTABLE_TABLE_NAME", "Questions")
airtable_table     = Table(AIRTABLE_TOKEN, AIRTABLE_BASE_ID, AIRTABLE_TABLE)

app = Flask(__name__)

@app.route('/interview-results', methods=['GET'])
def get_interview_results():
    try:
        # grab the last 10 inserted records, newest first
        resp = supabase\
            .table('interview_results')\
            .select('*')\
            .order('id', desc=True)\
            .limit(10)\
            .execute()
        
        # resp.data will be a list of dicts
        return jsonify(resp.data)
    except Exception as e:
        app.logger.error("Error fetching results: %s", e, exc_info=True)
        return jsonify({ "error": str(e) }), 500

@app.route('/questions', methods=['GET'])
def get_questions_file():
    """Serve the local questions.json to the React app."""
    try:
        with open('questions.json', 'r', encoding='utf-8') as f:
            qs = json.load(f)
        return jsonify(qs)
    except Exception as e:
        app.logger.error("Error reading questions.json", exc_info=True)
        return jsonify({"error": "Could not load questions"}), 500
    
def fetch_questions_from_airtable():
    """Fetch only active questions from Airtable with proper error handling"""
    try:
        # Correct filter formula syntax
        filter_formula = "AND({Active}, {Question} != '')"
        
        records = airtable_table.all(
            formula=filter_formula,
            sort=["Category", "Question"]  # Optional sorting
        )

        questions = []
        for rec in records:
            fields = rec.get("fields", {})
            questions.append({
                "id": rec.get("id"),  # Include record ID for reference
                "question": fields.get("Question", "").strip(),
            })
        
        return questions

    except InvalidParameterError as e:
        print(f"Invalid Airtable formula: {e}")
        return []  # Fallback to empty list
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def fetch_questions_from_file(filename: str):
    """Load questions from a local JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            qs = json.load(f)
        # ensure same shape
        return [
            {
                "id": q.get("id"),
                "question": q["question"],
            }
            for q in qs
            if q.get("question")
        ]
    except FileNotFoundError:
        app.logger.error(f"Questions file not found: {filename}")
        return []
    except json.JSONDecodeError as e:
        app.logger.error(f"Invalid JSON in {filename}: {e}")
        return []
    except Exception as e:
        app.logger.error("Error reading questions file", exc_info=True)
        return []

@app.route('/run-interview', methods=['POST'])
def run_interview_endpoint():
    try:
        data = request.get_json()
        provider = data.get('provider', 'openai')
        #raw_qs = fetch_questions_from_airtable()
        raw_qs = fetch_questions_from_file('questions.json')
        questions = [ q["question"] for q in raw_qs if q.get("question") ]
        results  = run_interview(load_agents(), questions,provider)
        RESULTS_FILE = 'results.json'
        try:
            with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                all_results = json.load(f)
                if not isinstance(all_results, list):
                    all_results = []
        except (FileNotFoundError, json.JSONDecodeError):
            all_results = []

        all_results.extend(results)

        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        for rec in results:
            rec["question"] = rec["question_en"]
            rec["answer"]   = rec["answer_en"]

        resp = supabase.table('interview_results').insert(results).execute()

        # If we get here, no exception was thrown → success
        return jsonify({
            "message": "Interview completed and saved successfully",
            "results": results,
            "inserted": resp.data  # echo back the rows Supabase saved
        })

    except Exception as e:
        app.logger.error("Interview endpoint error", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
