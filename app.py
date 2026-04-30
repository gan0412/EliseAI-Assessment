from flask import Flask, request, jsonify, render_template
import os
import requests
import time
import csv
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

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
APOLLO_API_KEY = os.environ.get("APOLLO_API_KEY", "")

def get_apollo_data(email, company_name):
    """
    Calls Apollo.io API to fetch exact employee count, revenue, and LinkedIn profile.
    """
    if not APOLLO_API_KEY:
        return "Apollo API Key not provided. Using default AI estimation."
        
    domain = email.split('@')[-1] if '@' in email else None
    if not domain or domain in ['gmail.com', 'yahoo.com', 'hotmail.com']:
        return f"Could not determine corporate domain for {company_name}."

    url = "https://api.apollo.io/v1/organizations/enrich"
    headers = {
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "X-Api-Key": APOLLO_API_KEY
    }
    payload = {
        "domain": domain
    }
    
    try:
        response = requests.get(url, headers=headers, params=payload)
        if response.status_code == 200:
            org = response.json().get('organization', {})
            if not org:
                return "No data found in Apollo for this domain."
            employees = org.get('estimated_num_employees', 'Unknown')
            revenue = org.get('annual_revenue', 'Unknown')
            linkedin = org.get('linkedin_url', 'Unknown')
            return f"Employees: {employees} | Est. Revenue: {revenue} | LinkedIn: {linkedin}"
        else:
            return f"Apollo API Error: {response.status_code}"
    except Exception as e:
        return f"Apollo Request Error: {e}"

def call_groq(prompt, max_tokens=500):
    """
    Calls the Groq API (using Llama 3) to generate text.
    """
    if not GROQ_API_KEY:
        return "ERROR: GROQ_API_KEY environment variable not set."
        
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "max_tokens": max_tokens,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        else:
            return f"ERROR: Groq HTTP {response.status_code} - {response.text}"
    except Exception as e:
        return f"ERROR: {e}"

@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "message": "EliseAI Webhook Server is running!",
        "instructions": "Send a POST request to /webhook/lead with a lead JSON payload to use the tool.",
        "dashboard": "Visit /dashboard to view enriched leads."
    }), 200

@app.route('/dashboard', methods=['GET'])
def dashboard():
    leads = []
    csv_file = "enriched_leads.csv"
    
    if os.path.exists(csv_file) and os.path.getsize(csv_file) > 0:
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                apollo_str = row.get('Apollo_Data', '')
                row['apollo_employees'] = 'N/A'
                row['apollo_revenue'] = 'N/A'
                row['apollo_linkedin'] = '#'
                
                if apollo_str and apollo_str != 'None':
                    parts = [p.strip() for p in apollo_str.split('|')]
                    for p in parts:
                        if p.startswith('Employees:'):
                            row['apollo_employees'] = p.replace('Employees:', '').strip()
                        elif p.startswith('Est. Revenue:'):
                            row['apollo_revenue'] = p.replace('Est. Revenue:', '').strip()
                        elif p.startswith('LinkedIn:'):
                            row['apollo_linkedin'] = p.replace('LinkedIn:', '').strip()
                leads.append(row)
                
    # Sort leads by priority descending (5 down to 1)
    def get_priority_val(x):
        try:
            return int(str(x.get("Priority", "1")).strip()[0])
        except ValueError:
            return 1
            
    leads.sort(key=get_priority_val, reverse=True)
    
    return render_template('dashboard.html', leads=leads)

@app.route('/assign', methods=['POST'])
def assign_lead():
    data = request.json
    email = data.get('email')
    assignee = data.get('assignee')
    
    csv_file = "enriched_leads.csv"
    if not os.path.exists(csv_file):
        return jsonify({"status": "error", "message": "CSV not found"}), 400
        
    rows = []
    fieldnames = []
    updated_draft = ""
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        if 'Assignee' not in fieldnames:
            fieldnames.append('Assignee')
        for row in reader:
            if row.get('Email Address') == email:
                old_assignee = row.get('Assignee', '')
                
                # Extract first name (e.g. 'Alice (Senior SDR)' -> 'Alice')
                new_name = assignee.split(' ')[0] if assignee else '[Your Name]'
                old_name = old_assignee.split(' ')[0] if old_assignee else '[Your Name]'
                
                row['Assignee'] = assignee
                draft = row.get('Draft_Email', '')
                
                # Replace name in draft
                if old_name and old_name in draft:
                    draft = draft.replace(old_name, new_name)
                elif '[Your Name]' in draft:
                    draft = draft.replace('[Your Name]', new_name)
                    
                row['Draft_Email'] = draft
                updated_draft = draft
                
            if 'Assignee' not in row:
                row['Assignee'] = ''
            rows.append(row)
            
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    return jsonify({"status": "success", "updated_draft": updated_draft}), 200

@app.route('/update_email', methods=['POST'])
def update_email():
    data = request.json
    email = data.get('email')
    draft_email = data.get('draft_email')
    
    csv_file = "enriched_leads.csv"
    if not os.path.exists(csv_file):
        return jsonify({"status": "error", "message": "CSV not found"}), 400
        
    rows = []
    fieldnames = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            if row.get('Email Address') == email:
                row['Draft_Email'] = draft_email
            rows.append(row)
            
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    return jsonify({"status": "success"}), 200

@app.route('/remove_lead', methods=['POST'])
def remove_lead():
    data = request.json
    email = data.get('email')
    
    csv_file = "enriched_leads.csv"
    if not os.path.exists(csv_file):
        return jsonify({"status": "error", "message": "CSV not found"}), 400
        
    rows = []
    fieldnames = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        for row in reader:
            if row.get('Email Address') != email:
                rows.append(row)
                
    with open(csv_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    return jsonify({"status": "success"}), 200

@app.route('/lead_count', methods=['GET'])
def lead_count():
    csv_file = "enriched_leads.csv"
    if not os.path.exists(csv_file):
        return jsonify({"count": 0}), 200
        
    count = 0
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        count = sum(1 for row in reader)
        if count > 0: count -= 1 # subtract header
        
    return jsonify({"count": count}), 200

@app.route('/webhook/lead', methods=['POST'])
def process_lead():
    """
    Webhook endpoint to process a single inbound lead payload.
    """
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "Invalid JSON payload"}), 400
        
    name = data.get("Name", "Unknown")
    email = data.get("Email Address", "")
    company = data.get("Company", "Unknown")
    address = data.get("Property Address", "Unknown")
    city = data.get("City", "Unknown")
    state = data.get("State", "Unknown")
    
    print(f"\n[Webhook Received] Processing Lead: {name} at {company}")

    # --- STEP 1: Apollo Enrichment ---
    print("  -> Step 1a: Fetching data from Apollo...")
    apollo_data = get_apollo_data(email, company)
    print(f"     Apollo Result: {apollo_data}")

    # --- STEP 2: Gather Information (Research) ---
    print("  -> Step 1b: Gathering insights via Groq (Llama 3)...")
    step1_prompt = f"""
    You are an expert real estate and property management researcher. 
    Analyze the following company and property location:
    Company Name: {company}
    Property Address: {address}, {city}, {state}
    Apollo Firmographic Data: {apollo_data}

    Please provide a concise analysis answering these three points:
    1. Company Intro: What does this company do? (Brief summary)
    2. Company Size: Estimate their size, total worth, and number of units/renters they manage.
    3. Property Size/Value: Estimate the value or tier of properties in {city}, {state}.
    
    Output strictly as plain text.
    """
    research_data = call_groq(step1_prompt, max_tokens=400)
    
    if "ERROR" in research_data:
        return jsonify({"status": "error", "message": research_data}), 500
        
    # Small sleep to ensure we don't hit rate limits on free API tiers
    time.sleep(1) 
    
    # --- STEP 3: Score and Draft Email ---
    print("  -> Step 2: Scoring and drafting email via Groq...")
    step2_prompt = f"""
    You are a top-performing Sales Development Representative (SDR) at EliseAI. 
    EliseAI sells premium AI assistants for property managers to handle leasing and resident communications.
    
    Here is the research on a new inbound lead:
    Lead Name: {name}
    Company: {company}
    
    Research Context:
    {research_data}
    
    Based on this context, do two things:
    1. PRIORITY JUDGMENT: Score the lead priority strictly as exactly one integer from 1 to 5 (1 = lowest priority, 5 = highest priority). 
       - Evaluate priority by explicitly looking at the Employee count, Annual Revenue, and portfolio size.
       - 5 = Massive enterprise property manager (e.g., >1,000 employees, >$50M revenue, or thousands of units).
       - 4 = Large regional property manager (e.g., 250-1,000 employees).
       - 3 = Mid-sized regional property manager (e.g., 50-250 employees).
       - 2 = Small team or boutique manager (10-50 employees).
       - 1 = Individual owner, very small team (<10 employees), or irrelevant company.
    2. DRAFT EMAIL: Write a highly concise, personalized outreach email to {name}. 
       - DO NOT explicitly mention any specific numbers (like exact employee count, revenue, or unit numbers) as it sounds unnatural for a cold email.
       - Instead, casually allude to their scale (e.g. "enterprise scale", "regional presence", or "local operations") based on the research.
       - Assume they are an inbound lead who already knows what EliseAI is. Skip any long introductory explanations of what we do. Get straight to the value we provide for their specific scale.
       - End the email with this EXACT signature format:
         Best regards,
         [Your Name]
         www.eliseai.com
    
    Format your response EXACTLY like this:
    PRIORITY: [Your Priority Number (1-5)]
    ---
    [Your Email Draft]
    """
    
    final_output = call_groq(step2_prompt, max_tokens=400)
    
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
    
    # --- Auto-Save to CSV for Dashboard ---
    csv_file = "enriched_leads.csv"
    file_exists = os.path.exists(csv_file) and os.path.getsize(csv_file) > 0
    
    row = {
        "Name": name,
        "Email Address": email,
        "Company": company,
        "Property Address": address,
        "City": city,
        "State": state,
        "Priority": priority,
        "Apollo_Data": apollo_data,
        "Sales_Insights": research_data,
        "Draft_Email": email_draft,
        "Assignee": ""
    }
    
    fieldnames = list(row.keys())
    if file_exists:
        with open(csv_file, mode='r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if headers:
                fieldnames = headers
                for k in row.keys():
                    if k not in fieldnames:
                        fieldnames.append(k)

    with open(csv_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    
    # --- Return Final JSON Payload ---
    return jsonify({
        "status": "success",
        "original_lead": data,
        "enriched_data": {
            "Priority": priority,
            "Apollo_Data": apollo_data,
            "Sales_Insights": research_data,
            "Draft_Email": email_draft
        }
    }), 200

if __name__ == '__main__':
    print("Starting EliseAI Lead Webhook Server on port 5000...")
    app.run(port=5000)
