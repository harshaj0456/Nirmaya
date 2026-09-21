"""
Simulated external integrations: a real EDC system, ABDM/ABHA linkage,
and FHIR. Real endpoints require signed agreements and credentials we
obviously don't have for a hackathon prototype, so this module simulates
the *shape* of the integration - a sync action that behaves the way the
real one would - so the architecture can be demoed convincingly and
swapped for a live connection later without changing the API contract.
"""
import random
from datetime import datetime, timezone

INTEGRATION_STATUS = {
    "edc": {
        "connected": True,
        "system": "Simulated EDC (OpenClinica-style electronic data capture)",
        "last_sync": None,
    },
    "abdm": {
        "connected": True,
        "system": "Simulated ABDM Health Facility Registry / ABHA ID linkage",
        "last_sync": None,
    },
    "fhir": {
        "connected": True,
        "system": "Illustrative HL7 FHIR R4 export (hand-built Bundle, not a full FHIR server)",
        "last_sync": None,
    },
}

_SYMPTOMS = ["Mild rash", "Fatigue", "Loose stools", "Insomnia", "Dry mouth"]
_SITES = ["AIIA Delhi", "NIA Jaipur", "IPGT&RA Jamnagar"]


def simulate_edc_sync(ae_reports, trial_ids):
    """Simulates a new AE record arriving from an external EDC feed."""
    new_id = max((r["id"] for r in ae_reports), default=0) + 1
    record = {
        "id": new_id,
        "trial_id": random.choice(trial_ids),
        "site": random.choice(_SITES),
        "symptom": random.choice(_SYMPTOMS),
        "severity": "Mild",
        "date": datetime.now(timezone.utc).date().isoformat(),
        "serious": False,
        "meddra_code": "PENDING-CODING",
        "whodrug_code": "PENDING-CODING",
        "source": "EDC_SYNC",
    }
    ae_reports.append(record)
    INTEGRATION_STATUS["edc"]["last_sync"] = datetime.now(timezone.utc).isoformat()
    INTEGRATION_STATUS["abdm"]["last_sync"] = datetime.now(timezone.utc).isoformat()
    return record
