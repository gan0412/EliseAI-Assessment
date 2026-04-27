from flask import Flask, request, jsonify
import os
import requests
import time

# Load environment variables from .env.local manually
env_file = ".env.local"
if os.path.exists(env_file):
    with open(env_file, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

def call_claude(prompt, max_tokens=300):
    """
    Helper function to call the Anthropic API.
    """
    if not ANTHROPIC_API_KEY:
        return "ERROR: ANTHROPIC_API_KEY environment variable not set. Please set it before starting the server."
        
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            return response.json()['content'][0]['text']
        else:
            return f"API Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Request Error: {e}"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "EliseAI Webhook Server is running!",
        "instructions": "Send a POST request to /webhook/lead with a lead JSON payload to use the tool."
    }), 200

@app.route('/webhook/lead', methods=['POST'])
def process_lead():
    """
    Webhook endpoint to process a single inbound lead payload.
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
        
    name = data.get("Name", "Unknown")
    company = data.get("Company", "Unknown")
    address = data.get("Property Address", "Unknown")
    city = data.get("City", "Unknown")
    state = data.get("State", "Unknown")
    
    print(f"\n[Webhook Received] Processing Lead: {name} at {company}")

    # --- STEP 1: Gather Information (Research) ---
    print("  -> Step 1: Gathering insights via Claude...")
    step1_prompt = f"""
    You are an expert real estate and property management researcher. 
    Analyze the following company and property location:
    Company Name: {company}
    Property Address: {address}, {city}, {state}

    Please provide a concise analysis answering these three points:
    1. Company Intro: What does this company do? (Brief summary)
    2. Company Size: Estimate their size, total worth, and number of units/renters they manage.
    3. Property Size/Value: Estimate the value or tier of properties in {city}, {state}.
    
    Output strictly as plain text.
    """
    research_data = call_claude(step1_prompt, max_tokens=400)
    
    if "ERROR" in research_data:
        return jsonify({"status": "error", "message": research_data}), 500
        
    # Small sleep to ensure we don't hit rate limits on free API tiers
    time.sleep(1) 
    
    # --- STEP 2: Score and Draft Email ---
    print("  -> Step 2: Scoring and drafting email via Claude...")
    step2_prompt = f"""
    You are a top-performing Sales Development Representative (SDR) at EliseAI. 
    EliseAI sells premium AI assistants for property managers to handle leasing and resident communications.
    
    Here is the research on a new inbound lead:
    Lead Name: {name}
    Company: {company}
    
    Research Context:
    {research_data}
    
    Based on this context, do two things:
    1. PRIORITY JUDGMENT: Score the lead priority strictly as exactly one of: [LOW, MEDIUM, HIGH]. 
       - HIGH = Massive enterprise property manager (thousands of units).
       - MEDIUM = Mid-sized regional property manager.
       - LOW = Individual owner or irrelevant company.
    2. DRAFT EMAIL: Write a short, personalized outreach email to {name} referencing their company size/location and explaining how EliseAI can help them automate their specific scale of operations.
    
    Format your response EXACTLY like this:
    PRIORITY: [Your Priority]
    ---
    [Your Email Draft]
    """
    
    final_output = call_claude(step2_prompt, max_tokens=300)
    
    # Parse the output
    priority = "UNKNOWN"
    email_draft = final_output
    if "PRIORITY:" in final_output:
        parts = final_output.split("---")
        priority_line = parts[0].strip()
        priority = priority_line.replace("PRIORITY:", "").strip()
        if len(parts) > 1:
            email_draft = parts[1].strip()
            
    print(f"  -> Successfully processed! Priority: {priority}")
    
    # --- Return Final JSON Payload ---
    return jsonify({
        "status": "success",
        "original_lead": data,
        "enriched_data": {
            "Priority": priority,
            "Sales_Insights": research_data,
            "Draft_Email": email_draft
        }
    }), 200

if __name__ == '__main__':
    print("Starting EliseAI Lead Webhook Server on port 5000...")
    app.run(port=5000)
