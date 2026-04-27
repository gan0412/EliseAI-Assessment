import csv
import requests
import os

WEBHOOK_URL = "http://127.0.0.1:5000/webhook/lead"
INPUT_CSV = "leads.csv"
OUTPUT_CSV = "enriched_leads.csv"

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"Error: Could not find {INPUT_CSV}")
        return

    enriched_rows = []
    
    print(f"Reading {INPUT_CSV} and sending to webhook...")
    with open(INPUT_CSV, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(f"Processing: {row['Company']}...")
            try:
                # Send the row to our webhook API
                response = requests.post(WEBHOOK_URL, json=row, headers={"Content-Type": "application/json"})
                if response.status_code == 200:
                    data = response.json()
                    enriched_data = data.get("enriched_data", {})
                    
                    # Add the new AI data to our row
                    row["Priority"] = enriched_data.get("Priority", "Unknown")
                    row["Sales_Insights"] = enriched_data.get("Sales_Insights", "Error")
                    row["Draft_Email"] = enriched_data.get("Draft_Email", "Error")
                    
                    enriched_rows.append(row)
                else:
                    print(f"  -> Failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"  -> Error: {e}")

    if enriched_rows:
        # Sort by Priority (HIGH -> MEDIUM -> LOW)
        priority_map = {"HIGH": 1, "MEDIUM": 2, "LOW": 3}
        enriched_rows.sort(key=lambda x: priority_map.get(x.get("Priority", "LOW"), 4))

        print(f"\nWriting results to {OUTPUT_CSV}...")
        fieldnames = list(enriched_rows[0].keys())
        with open(OUTPUT_CSV, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(enriched_rows)
            
        print("Done! Open enriched_leads.csv to see the results.")

if __name__ == "__main__":
    main()
