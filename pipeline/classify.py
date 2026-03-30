"""
Classification engine for AI Governance Tracker.

Three functions:
1. is_ai_relevant() — keyword filter to determine if an entry is AI-related
2. tag_domains() — assigns domain tags based on keyword presence
3. normalize_status() — maps raw status strings to a common taxonomy
"""

import re
import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# AI Relevance Keywords
# ---------------------------------------------------------------------------
# An entry is AI-related if its title or summary contains any of these.
# Uses word-boundary matching to reduce false positives.

AI_KEYWORDS = [
    # English
    "artificial intelligence",
    "machine learning",
    "automated decision",
    "algorithmic",
    "deep learning",
    "neural network",
    "generative ai",
    "large language model",
    "foundation model",
    "autonomous system",
    "facial recognition",
    "biometric",
    "predictive analytics",
    "robotic",
    "robotics",
    "deepfake",
    "chatbot",
    "computer vision",
    # French (for Canadian bilingual content)
    "intelligence artificielle",
    "apprentissage automatique",
    "apprentissage profond",
    "reconnaissance faciale",
    "réseau neuronal",
    "véhicule autonome",
    "décision automatisée",
    "système autonome",
]

# Compile regex patterns once for performance (word-boundary, case-insensitive)
AI_PATTERNS = [re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in AI_KEYWORDS]

# "AI" alone is tricky — matches "avian influenza", "Amnesty International", etc.
# Only match standalone "AI" if it appears near a context word.
AI_CONTEXT_WORDS = [
    "system", "model", "regulation", "act", "governance", "safety",
    "risk", "transparency", "accountability", "compliance", "deploy",
    "train", "bias", "ethical", "framework", "audit", "algorithm",
    "technology", "digital", "data", "automat",
]
AI_STANDALONE_PATTERN = re.compile(r"\bAI\b")
AI_CONTEXT_PATTERNS = [re.compile(r"\b" + re.escape(w), re.IGNORECASE) for w in AI_CONTEXT_WORDS]

# ---------------------------------------------------------------------------
# Domain Tagging
# ---------------------------------------------------------------------------

DOMAIN_KEYWORDS = {
    "Healthcare": [
        "health", "medical", "patient", "clinical", "drug",
        "pharmaceutical", "diagnostic", "hospital", "therapy",
        "santé", "médical",
    ],
    "Employment": [
        "employment", "hiring", "worker", "workplace", "labour",
        "labor", "recruitment", "termination", "job", "wage",
        "emploi", "travailleur",
    ],
    "Criminal Justice": [
        "criminal", "policing", "surveillance", "law enforcement",
        "sentencing", "bail", "parole", "prison", "incarceration",
        "police", "détention",
    ],
    "Privacy": [
        "privacy", "data protection", "personal information",
        "biometric", "consent", "gdpr", "pipeda", "surveillance",
        "confidentialité", "données personnelles",
    ],
    "Financial Services": [
        "banking", "financial", "credit", "insurance", "fintech",
        "lending", "securities", "investment",
        "bancaire", "financier",
    ],
    "Education": [
        "education", "student", "school", "academic", "university",
        "classroom", "teacher",
        "éducation", "étudiant",
    ],
    "Transportation": [
        "autonomous vehicle", "self-driving", "transportation",
        "drone", "aviation", "traffic",
        "véhicule autonome", "transport",
    ],
    "Defence/National Security": [
        "defence", "defense", "military", "national security",
        "intelligence agency", "cybersecurity", "cyber security",
        "défense", "sécurité nationale",
    ],
}

# Compile domain patterns
DOMAIN_PATTERNS = {}
for domain, keywords in DOMAIN_KEYWORDS.items():
    DOMAIN_PATTERNS[domain] = [
        re.compile(r"\b" + re.escape(kw) + r"\b", re.IGNORECASE) for kw in keywords
    ]

# ---------------------------------------------------------------------------
# Status Normalization
# ---------------------------------------------------------------------------

# Per-jurisdiction mapping tables
STATUS_MAPS = {
    "US-FED": {
        "introduced": "Proposed",
        "referred to committee": "Proposed",
        "reported by committee": "In Progress",
        "passed house": "In Progress",
        "passed senate": "In Progress",
        "resolving differences": "In Progress",
        "to president": "In Progress",
        "became law": "In Force",
        "signed by president": "Passed/Adopted",
        "enacted": "In Force",
        "vetoed": "Withdrawn/Defeated",
        "failed": "Withdrawn/Defeated",
    },
    "CA-FED": {
        "first reading": "Proposed",
        "introduction and first reading": "Proposed",
        "second reading": "In Progress",
        "committee": "In Progress",
        "report stage": "In Progress",
        "third reading": "In Progress",
        "passed": "In Progress",
        "royal assent": "Passed/Adopted",
        "in force": "In Force",
        "defeated": "Withdrawn/Defeated",
        "withdrawn": "Withdrawn/Defeated",
        "prorogued": "Withdrawn/Defeated",
    },
    "CA-ON": {
        "first reading": "Proposed",
        "second reading": "In Progress",
        "committee": "In Progress",
        "third reading": "In Progress",
        "royal assent": "Passed/Adopted",
        "in force": "In Force",
        "withdrawn": "Withdrawn/Defeated",
    },
    "EU": {
        "proposal": "Proposed",
        "proposed": "Proposed",
        "under negotiation": "In Progress",
        "adopted": "Passed/Adopted",
        "published": "Passed/Adopted",
        "in force": "In Force",
        "entered into force": "In Force",
        "repealed": "Withdrawn/Defeated",
        "withdrawn": "Withdrawn/Defeated",
    },
}


def is_ai_relevant(title, summary=""):
    """
    Check if an entry is AI-related based on keyword matching.

    Prefers false positives over false negatives — it's better to include
    a borderline entry than miss a real one.

    Args:
        title: The entry's title
        summary: The entry's summary or description text

    Returns:
        True if the entry appears AI-related
    """
    text = f"{title} {summary}"

    # Check multi-word AI keywords
    for pattern in AI_PATTERNS:
        if pattern.search(text):
            return True

    # Check standalone "AI" only with context words nearby
    if AI_STANDALONE_PATTERN.search(text):
        for ctx_pattern in AI_CONTEXT_PATTERNS:
            if ctx_pattern.search(text):
                return True

    return False


def tag_domains(title, summary=""):
    """
    Tag an entry with one or more domain categories.

    Returns all matching domains. If none match, returns ["General"].

    Args:
        title: The entry's title
        summary: The entry's summary or description text

    Returns:
        List of domain name strings
    """
    text = f"{title} {summary}"
    matched = []

    for domain, patterns in DOMAIN_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(text):
                matched.append(domain)
                break  # one match per domain is enough

    return matched if matched else ["General"]


def normalize_status(raw_status, jurisdiction_code):
    """
    Normalize a raw status string to the common taxonomy.

    Taxonomy: Proposed, In Progress, Passed/Adopted, In Force, Withdrawn/Defeated

    Args:
        raw_status: The status string from the data source
        jurisdiction_code: e.g., "US-FED", "CA-FED", "EU"

    Returns:
        Normalized status string
    """
    if not raw_status:
        return "Proposed"

    status_lower = raw_status.lower().strip()

    # Try jurisdiction-specific map first
    jur_map = STATUS_MAPS.get(jurisdiction_code, {})
    for key, normalized in jur_map.items():
        if key in status_lower:
            return normalized

    # Try all maps as fallback
    for jur, jur_map in STATUS_MAPS.items():
        for key, normalized in jur_map.items():
            if key in status_lower:
                return normalized

    # Check if it's already a normalized value
    normalized_values = {"Proposed", "In Progress", "Passed/Adopted", "In Force", "Withdrawn/Defeated"}
    if raw_status in normalized_values:
        return raw_status

    logger.warning(
        f"Unknown status '{raw_status}' for jurisdiction {jurisdiction_code}, "
        f"defaulting to 'Proposed'"
    )
    return "Proposed"


def classify_entry(entry):
    """
    Run the full classification pipeline on an entry.

    Sets the 'domains' and 'status' fields based on keyword analysis.
    This mutates the entry dict in place and returns it.

    Args:
        entry: An entry dict following the project schema

    Returns:
        The entry dict with domains and status fields populated
    """
    title = entry.get("title", "")
    summary = entry.get("summary", "")

    # Tag domains
    entry["domains"] = tag_domains(title, summary)

    # Normalize status (only if not already normalized by the source)
    raw_status = entry.get("status", "")
    jurisdiction_code = entry.get("jurisdiction_code", "")
    entry["status"] = normalize_status(raw_status, jurisdiction_code)

    return entry
