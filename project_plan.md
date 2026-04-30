# EliseAI Lead Enrichment Tool: Project Rollout Plan

## 1. Testing the MVP

Before deploying this webhook-based tool to the entire sales organization, we need to ensure the AI logic (via Groq/Llama 3) produces accurate, high-quality outputs that SDRs trust.

- **Data Integrity Check:** Run the `test_trigger.py` script locally to send a batch of historical, known leads through the `/webhook/lead` endpoint. 
- **Blind Review:** Have 2-3 top-performing SDRs review the AI-generated Priority (1-5) and Outreach Emails without knowing it was AI-generated. Compare Groq's priority with the actual closed-won or closed-lost outcome of those historical leads.
- **Prompt Refinement:** Adjust the Groq prompts in `app.py` if the SDRs feel the emails sound too robotic or if the Priority scoring is inaccurate.

## 2. Process to Roll It Out

We will use a phased approach to integrate this webhook into the CRM (Salesforce or Hubspot).

- **Phase 1 (Shadow Mode):** Deploy `app.py` to a secure internal server. Configure a CRM automation rule that sends an HTTP POST request to this webhook every time a new inbound lead is created. The resulting JSON payload is saved to hidden "Staging Priority" and "Staging Insights" fields on the Lead record. SDR Managers review this daily to monitor performance, but SDRs continue their manual process.
- **Phase 2 (Beta Group):** 3 selected SDRs have the webhook data exposed in their CRM page layouts. Instead of researching leads manually, they see the `Priority` and `Company Intro` prominently on the lead record, and the `Draft_Email` is pre-populated in their email sequencing tool (e.g., Outreach/SalesLoft).
- **Phase 3 (Full Integration):** The webhook is pushed to production for all incoming leads. Webhook data drives routing logic (e.g., HIGH priority leads are instantly routed to the most senior SDRs). 

## 3. Timelines

- **Week 1:** Webhook Development, internal testing, and historical data validation (MVP Testing).
- **Week 2:** Phase 1 (Shadow Mode). Webhook is active in CRM; SDR Managers audit the hidden fields. Prompt tuning based on real inbound lead edge cases.
- **Week 3:** Phase 2 (Beta Group). 3 SDRs use the tool exclusively. Collect feedback on time saved per lead and response rates of the drafted emails.
- **Week 4:** Phase 3 (Full Integration). Expose data to the entire sales org and implement Priority-based lead routing.

## 4. Key Stakeholders (Internal)

- **SDR Manager / VP of Sales:** To align on the definition of a "Priority 5" lead and approve the core messaging framework in the AI prompt.
- **Sales Operations (RevOps):** To assist with setting up the CRM Webhook triggers, creating the custom fields to store the JSON data, and building the lead routing logic in Phase 3.
- **Legal / Compliance:** To ensure sending PII (Lead Name/Email/Address) to external APIs complies with EliseAI's data privacy policies.
- **The SDR Team:** The end-users. We must prove the tool saves them time and increases their meeting booked rate.
