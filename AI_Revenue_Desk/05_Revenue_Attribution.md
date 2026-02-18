# AI Revenue Desk™ — Weekly Revenue Attribution System

## 1. Revenue Tracking Model
To ensure maximum ROI transparency, we bridge the gap between the **AI Interaction** and the **CRM Job Invoice**.

1.  **Lead Origin:** AI tags every booking/recovery with a unique `AI_TRACKING_ID`.
2.  **CRM Match:** When a job is closed in ServiceTitan/Salesforce, we pull the `Invoice_Total` where the tag matches.
3.  **Attribution:** 100% of that revenue is attributed to the AI Revenue Desk if the lead was handled by AI before the first human tech visit.

## 2. ROI Calculation Formula
*   **Gross AI Revenue:** Total $ from jobs booked/recovered by AI.
*   **Operating Cost:** (Monthly Retainer) + (API Usage Fees).
*   **ROI %:** `((Gross AI Revenue - Operating Cost) / Operating Cost) * 100`
*   **Cost Per Booking (CPB):** `Operating Cost / Total Number of Bookings`

## 3. Sample Weekly Client Report (Executive Summary)

**Date Range:** June 1st – June 7th
**Client:** Peak Performance HVAC

### Executive Summary
> "This week, AI Revenue Desk™ handled 44 calls, successfully booking 12 new jobs and recovering 5 missed calls that would have otherwise gone to competitors. This resulted in an estimated **$14,500 in attributed revenue**."

### KPI Overview
| Metric | Result | vs Previous Week |
| :--- | :--- | :--- |
| **Total Calls Answered** | 44 | +10% |
| **New Bookings** | 12 | +2 |
| **Missed Call Recoveries** | 5 | +1 |
| **AI Booking Rate** | 38.6% | +2.1% |
| **Est. Attributed Revenue** | $14,500 | +$3,200 |
| **ROI (Weekly)** | 7.25x | +0.5x |

### Performance Improvement Suggestions
*   **Observation:** 4 callers hung up during the "Diagnostic Fee" mention.
*   **Suggestion:** We are testing a script iteration that emphasizes the "Fee waived with repair" earlier in the flow to reduce churn at the pricing stage.

## 4. Dashboard Layout (Visual Requirements)
*   **Hero Stat:** Large Green "$14,500" (Total Revenue Booked).
*   **Live Feed:** Real-time log of AI transcriptions and recordings.
*   **Heatmap:** What time of day is the AI most active? (Helps client adjust human staffing if needed).
*   **Funnel:** Calls -> Qualified -> Booked -> Invoiced.

## 5. CRM Data Fields (Required Custom Fields)
*   `AI_Lead_ID`: (String)
*   `AI_Interaction_Log`: (Long Text/URL)
*   `AI_Booking_Status`: (Dropdown: Booked, Recovered, Follow-up Required)
*   `AI_Revenue_Attributed`: (Currency)
