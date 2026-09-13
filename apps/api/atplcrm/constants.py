STAGES = [
    ("discovery", "Discovery & qualification"),
    ("presales", "Pre-sales & solutioning"),
    ("proposal", "Proposal submitted"),
    ("negotiation", "Negotiation"),
    ("contract", "Contract & purchase order"),
    ("won", "Closed won"),
    ("lost", "Closed lost"),
    ("hold", "On hold / nurture"),
]
PROBABILITIES = dict(zip((item[0] for item in STAGES), [20, 35, 50, 70, 85, 100, 0, 0], strict=True))
LEAD_STATUSES = [("new", "New"), ("working", "Working"), ("engaged", "Engaged"), ("ready", "Ready for validation"), ("closed", "Closed")]
BLOCKERS = ["None", "Customer response", "Internal sales", "Pre-sales", "Technical", "Proposal", "Pricing", "Legal", "Procurement", "Budget", "Partner", "Management", "Other"]
SOURCES = ["Outbound email", "Outbound call", "LinkedIn", "Exhibition or event", "Webinar", "Marketing campaign", "Inbound website enquiry", "Referral from client", "Referral from partner", "Existing client expansion", "Analyst or press", "Other"]
SERVICES = ["AI strategy & advisory", "AI & ML delivery", "Agentic AI & platform", "Data engineering", "Executive enablement", "Managed services & AMC"]
ACTIONS = ["Call", "Email", "LinkedIn", "Meeting", "Demo", "Proposal", "Follow up", "Internal review", "Other"]
LOSS_REASONS = ["Price", "Lost to competitor", "No budget", "Project cancelled", "Customer delayed indefinitely", "Relationship", "Technical fit", "Client built internally", "Lost to incumbent partner", "No response", "Disqualified by Soothsayer"]
DISQUALIFY_REASONS = ["No genuine requirement", "Outside capability", "No budget", "Wrong seniority of contact", "Timing not viable", "Duplicate", "Conflict of interest", "No response"]
REQUEST_STATUSES = ["Requested", "Clarification required", "Accepted", "In progress", "Ready for review", "Approved to share", "Delivered", "Blocked", "Cancelled"]
MANAGEMENT = {"Administrator", "Executive", "Manager"}

COMPANY_TYPES = ["Client", "Prospect", "Referral partner", "Reseller", "Local partner", "Prime contractor", "Subcontractor"]
CONTACT_SENIORITIES = ["C-level", "VP or Head", "Director", "Manager", "Individual contributor", "Unknown"]
ENGAGEMENT_STATUSES = ["Not contacted", "Contacted no response", "Engaged", "Meeting held", "Unresponsive", "Do not contact"]
CONSENT_BASES = ["Business card or event", "Referral", "Public professional profile", "Inbound enquiry", "Existing client relationship"]
ACTIVITY_TYPES = ["Email", "Call", "LinkedIn message", "LinkedIn connection request", "WhatsApp", "Meeting", "Demo", "Workshop", "Event conversation", "Internal note"]
ACTIVITY_OUTCOMES = ["No response", "Responded", "Meeting booked", "Referred onward", "Declined", "Not relevant"]

REFERENCE_DEFAULTS = {
    "stages": [(code, label, PROBABILITIES[code]) for code, label in STAGES],
    "lead_statuses": [(code, label, None) for code, label in LEAD_STATUSES],
    "sources": [(value, value, None) for value in SOURCES],
    "services": [(value, value, None) for value in SERVICES],
    "actions": [(value, value, None) for value in ACTIONS],
    "blockers": [(value, value, None) for value in BLOCKERS],
    "loss_reasons": [(value, value, None) for value in LOSS_REASONS],
    "disqualification_reasons": [(value, value, None) for value in DISQUALIFY_REASONS],
    "request_statuses": [(value, value, None) for value in REQUEST_STATUSES],
}
LOCKED_REFERENCE_CATEGORIES = {"stages", "lead_statuses", "request_statuses"}
