import requests
import json
import time

WEBHOOK_URL = "http://127.0.0.1:5000/webhook/lead"

# We will simulate 3 different leads arriving at the webhook
test_leads = [
    {
        "Name": "John Doe",
        "Email Address": "john.doe@greystar.com",
        "Company": "Greystar",
        "Property Address": "123 Main St",
        "City": "Dallas",
        "State": "TX",
        "Country": "USA"
    },
    {
        "Name": "Jane Smith",
        "Email Address": "jane@avalonbay.com",
        "Company": "AvalonBay Communities",
        "Property Address": "456 Market St",
        "City": "San Francisco",
        "State": "CA",
        "Country": "USA"
    },
    {
        "Name": "Bob Johnson",
        "Email Address": "bob@smallprop.com",
        "Company": "Bob's Local Rentals",
        "Property Address": "789 Oak Ave",
        "City": "Springfield",
        "State": "IL",
        "Country": "USA"
    }
]

def main():
    print("--- EliseAI Webhook Trigger Test ---")
    print(f"Target URL: {WEBHOOK_URL}\n")
    
    for lead in test_leads:
        print(f"Sending payload for: {lead['Company']}...")
        
        try:
            response = requests.post(
                WEBHOOK_URL, 
                json=lead,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print("SUCCESS! Received Enriched Data:")
                print(f"  Priority: {data['enriched_data']['Priority']}")
                print(f"  Insights Length: {len(data['enriched_data']['Sales_Insights'])} chars")
                print(f"  Email Draft: {data['enriched_data']['Draft_Email'][:100]}...\n")
            else:
                print(f"Failed: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Error connecting to Webhook: {e}")
            print("Make sure app.py is running in another terminal window!")
            break
            
        time.sleep(2)

if __name__ == "__main__":
    main()
