# AI Revenue Desk™ — Delivery Framework

## The 14-Day "Rapid Response" Install Model

### PHASE 1 – Setup (Days 1–5)
*   **Day 1: Onboarding:** Client submits CRM access, pricing sheets, and current call flow.
*   **Day 2: Provisioning:** Provision Twilio numbers and link to custom Retell sub-account.
*   **Day 3: Voice Training:** Upload company SOPs, manuals, and common faqs to the AI LLM context.
*   **Day 4: Integration:** Build the n8n/Make pipelines to sync AI bookings with the client CRM.
*   **Day 5: QA Testing:** Run 50 automated test calls to verify edge case handling and booking logic.

### PHASE 2 – Deployment (Days 6–10)
*   **Day 6: Shadow Mode:** Route 10% of calls to AI; monitor live transcripts for accuracy.
*   **Day 7: Performance Tuning:** Adjust voice latency and tone based on initial feedback.
*   **Day 8: Full Go-Live:** Route all after-hours and overflow calls to AI Revenue Desk.
*   **Day 9: Reporting Setup:** Sync BigQuery/Sheets to the client's new Revenue Dashboard.
*   **Day 10: Staff Training:** 30-minute Zoom call with the client's team on how to handle AI-notified bookings.

### PHASE 3 – Optimization (Days 11–14)
*   **Day 11: A/B Testing:** Launch two variations of the SMS recovery message.
*   **Day 12: Revenue Sync:** Verify that the first booked jobs are showing up correctly in the attribution model.
*   **Day 14: Handover:** Final review of the week 1 report and baseline established.

---

## Team Roles
| Role | Responsibility |
| :--- | :--- |
| **Implementation Specialist** | System architecture, API connections, n8n flows. |
| **Conversation Designer** | Prompt engineering, voice agent tone, SMS scripts. |
| **Success Manager** | Client communication, reporting, weekly ROI audits. |

---

## Client Responsibilities
*   **Access:** Must provide Admin access to CRM (ServiceTitan, Salesforce, etc.).
*   **Data:** Must provide accurate pricing and "standard operating procedure" for bookings.
*   **Feedback:** Must review and approve the Voice Script during Phase 1.

## QA Checklist (Pre-Go-Live)
- [ ] AI correctly identifies a non-service area Zip Code.
- [ ] CRM Opportunity is created with all 5 mandatory fields.
- [ ] Emergency transfer dials out to the correct on-call number.
- [ ] SMS recovery trigger fires within 10 seconds of a missed call.
- [ ] Voice latency is under 1.8 seconds (Neural processing time).
