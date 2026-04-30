import requests
import json
import csv
import os

WEBHOOK_URL = "http://127.0.0.1:5000/webhook/lead"

def save_to_csv(lead_payload, enriched):
    csv_file = "enriched_leads.csv"
    file_exists = os.path.isfile(csv_file) and os.path.getsize(csv_file) > 0
    
    row = lead_payload.copy()
    row["Priority"] = enriched.get("Priority", "Unknown")
    row["Apollo_Data"] = enriched.get("Apollo_Data", "None")
    row["Sales_Insights"] = enriched.get("Sales_Insights", "Error")
    row["Draft_Email"] = enriched.get("Draft_Email", "Error")
    
    with open(csv_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)

def main():
    print("=====================================")
    print(" EliseAI Interactive Lead Tester")
    print("=====================================\n")
    print("Enter the details of the lead below:\n")
    
    name = input("Lead Name: ")
    email = input("Email Address: ")
    company = input("Company Name: ")
    address = input("Property Address: ")
    city = input("City: ")
    state = input("State: ")
    
    lead_payload = {
        "Name": name,
        "Email Address": email,
        "Company": company,
        "Property Address": address,
        "City": city,
        "State": state,
        "Country": "USA"
    }
    
    print("\nSending lead to Webhook Server...\n")
    
    try:
        response = requests.post(
            WEBHOOK_URL, 
            json=lead_payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            enriched = data.get('enriched_data', {})
            
            print("=====================================")
            print(" ✅ SUCCESS! Received Enriched Data ")
            print("=====================================")
            print(f"🏢 Apollo Firmographics : {enriched.get('Apollo_Data', 'None')}")
            print(f"⭐ Priority Score       : {enriched.get('Priority', 'Unknown')}")
            print(f"📊 Sales Insights       :\n{enriched.get('Sales_Insights', 'Error')}\n")
            print(f"📧 Drafted Email        :\n{enriched.get('Draft_Email', 'Error')}")
            print("=====================================\n")
            
            # Save to CSV
            save_to_csv(lead_payload, enriched)
            print("💾 Saved successfully to enriched_leads.csv!\n")
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error connecting to Webhook: {e}")
        print("Make sure app.py is running in another terminal window!")

if __name__ == "__main__":
    while True:
        main()
        cont = input("Test another lead? (y/n): ")
        if cont.lower() != 'y':
            break
