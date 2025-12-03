import os

class Settings:
    LEADMAGIC_API_KEY: str = os.getenv("LEADMAGIC_API_KEY", "")
    APOLLO_API_KEY: str = os.getenv("APOLLO_API_KEY", "")
    
    # Vayu Context
    VAYU_VALUE_PROP: str = "We help companies automate their BDR workflows with AI."
    VAYU_DIFFERENTIATORS: str = "Deep prospecting, context-aware outreach, and continuous learning."
    VAYU_DESCRIPTION: str = "Vayu is an AI-powered BDR that works 24/7."

settings = Settings()

VAYU_CONTEXT = {
    "name": "Vayu",
    "description": "Vayu is a usage-based billing and revenue operations platform designed specifically for B2B SaaS companies with complex pricing models.",
    "value_proposition": "We help companies automate their entire quote-to-cash process, eliminate billing errors, and provide real-time revenue visibility.",
    "differentiators": [
        "Built for usage-based and hybrid pricing models (not just simple subscriptions).",
        "Real-time metering and mediation engine.",
        "Seamless integration with CRM (Salesforce/HubSpot) and ERP (NetSuite/QuickBooks).",
        "Automated revenue recognition and reporting.",
    ],
    "target_audience": "B2B SaaS companies, especially those in AI, API-first, or Infrastructure sectors.",
    "tone": "Professional, innovative, helpful, and direct.",
}
