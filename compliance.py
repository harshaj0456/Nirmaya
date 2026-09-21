"""
DPDP consent tracking, electronic-signature ledger, and the compliance
"posture" summary (hosting/encryption/DPDP controls) the problem statement
asks the platform to satisfy.
"""
import hashlib
from datetime import datetime, timezone

CONSENT_LOG = []       # append-only history of consent state changes
ESIGNATURES = []       # hash-chained e-signature ledger


def _now():
    return datetime.now(timezone.utc).isoformat()


def record_consent(trial_id, subject_id, new_status, actor):
    """
    DPDP requires consent to be actively managed, not just captured once.
    Every change is appended, never overwritten, so a regulator can see
    the full consent history for a subject, including withdrawal.
    """
    entry = {
        "trial_id": trial_id,
        "subject_id": subject_id,
        "status": new_status,
        "recorded_by": actor,
        "timestamp": _now(),
    }
    CONSENT_LOG.append(entry)
    return entry


def capture_esignature(actor, role, meaning, record_type, record_id):
    """
    A hash-chained ledger: each signature's hash depends on the previous
    one, so any tampering with an earlier entry would break the chain -
    the same tamper-evidence idea real e-signature systems (e.g. Part 11
    -compliant systems) rely on, simplified for a prototype.
    """
    prior_hash = ESIGNATURES[-1]["hash"] if ESIGNATURES else "GENESIS"
    timestamp = _now()
    payload = f"{actor}|{role}|{meaning}|{record_type}|{record_id}|{prior_hash}|{timestamp}"
    sig_hash = hashlib.sha256(payload.encode()).hexdigest()[:20]
    entry = {
        "actor": actor,
        "role": role,
        "meaning": meaning,
        "record_type": record_type,
        "record_id": record_id,
        "timestamp": timestamp,
        "hash": sig_hash,
        "prior_hash": prior_hash,
    }
    ESIGNATURES.append(entry)
    return entry


def verify_chain():
    """Recomputes the hash chain to prove nothing in ESIGNATURES has been
    altered out of band - the point of a tamper-evident ledger."""
    prior_hash = "GENESIS"
    for entry in ESIGNATURES:
        payload = f"{entry['actor']}|{entry['role']}|{entry['meaning']}|{entry['record_type']}|{entry['record_id']}|{prior_hash}|{entry['timestamp']}"
        expected = hashlib.sha256(payload.encode()).hexdigest()[:20]
        if expected != entry["hash"] or entry["prior_hash"] != prior_hash:
            return False
        prior_hash = entry["hash"]
    return True


COMPLIANCE_POSTURE = {
    "hosting": {
        "region": "Simulated: ap-south-1 (Mumbai) - data-resident, per NDCT/DPDP hosting expectations",
        "iso27001": "Simulated control mapping for a prototype - not an actual certification",
        "cert_in": "Simulated CERT-In empanelment checklist - not an actual empanelment",
    },
    "encryption": {
        "at_rest": "Fernet symmetric encryption applied to subject-identifying fields (see security.py)",
        "in_transit": "Assumes HTTPS/TLS in a real deployment - not applicable on a localhost demo",
        "key_management": "Demo key is in-process only; production requires a managed KMS",
    },
    "dpdp_2023": {
        "consent_management": "Per-subject, timestamped, append-only consent log with withdrawal support",
        "data_minimisation": "Only clinically necessary fields are captured for the demo dataset",
        "purpose_limitation": "Data is scoped to the registered trial's protocol purpose only",
        "note": "This is a design demonstration, not a legal compliance certification",
    },
}
