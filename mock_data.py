"""
Seed data for the AIIA CTMS prototype.
In a real deployment this would live in a database (Postgres) with proper
audit-trail tables (ALCOA+). For the hackathon MVP we keep it in memory.
"""
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from security import encrypt

TODAY = date(2026, 9, 19)


def _d(days_from_today):
    return (TODAY + timedelta(days=days_from_today)).isoformat()


TRIALS = [
    {
        "id": "AIIA-CT-001",
        "title": "Ashwagandha Root Extract in Generalized Anxiety Disorder",
        "phase": "Phase II",
        "type": "Interventional",
        "ctri_number": "CTRI/2026/03/054321",
        "ctri_last_updated": _d(-40),
        "ethics_status": "Approved",
        "ethics_approval_date": _d(-120),
        "status": "Active",
        "target_enrollment": 120,
        "current_enrollment": 74,
        "sites": ["AIIA Delhi", "NIA Jaipur"],
        "next_monitoring_visit": _d(6),
        "protocol_deviations": 2,
        "data_query_open": 5,
        "principal_investigator": "Dr. R. Sharma",
    },
    {
        "id": "AIIA-CT-002",
        "title": "Triphala Churna for Functional Dyspepsia: Multi-Centre RCT",
        "phase": "Phase III",
        "type": "Interventional",
        "ctri_number": "CTRI/2025/11/049880",
        "ctri_last_updated": _d(-210),
        "ethics_status": "Renewal Due",
        "ethics_approval_date": _d(-360),
        "status": "Active",
        "target_enrollment": 300,
        "current_enrollment": 288,
        "sites": ["AIIA Delhi", "IPGT&RA Jamnagar", "NIA Jaipur"],
        "next_monitoring_visit": _d(-3),
        "protocol_deviations": 6,
        "data_query_open": 14,
        "principal_investigator": "Dr. M. Iyer",
    },
    {
        "id": "AIIA-CT-003",
        "title": "Observational Study: Panchakarma Outcomes in Chronic Low Back Pain",
        "phase": "Observational",
        "type": "Observational",
        "ctri_number": "CTRI/2026/06/058112",
        "ctri_last_updated": _d(-15),
        "ethics_status": "Approved",
        "ethics_approval_date": _d(-60),
        "status": "Enrolling",
        "target_enrollment": 200,
        "current_enrollment": 41,
        "sites": ["AIIA Delhi"],
        "next_monitoring_visit": _d(20),
        "protocol_deviations": 0,
        "data_query_open": 2,
        "principal_investigator": "Dr. A. Nair",
    },
    {
        "id": "AIIA-CT-004",
        "title": "Guggulu-Based Formulation in Dyslipidaemia: Safety Follow-up",
        "phase": "Phase IV",
        "type": "Interventional",
        "ctri_number": "CTRI/2024/08/041207",
        "ctri_last_updated": _d(-190),
        "ethics_status": "Approved",
        "ethics_approval_date": _d(-500),
        "status": "Closing Out",
        "target_enrollment": 80,
        "current_enrollment": 80,
        "sites": ["AIIA Delhi"],
        "next_monitoring_visit": None,
        "protocol_deviations": 1,
        "data_query_open": 0,
        "principal_investigator": "Dr. R. Sharma",
    },
]

# Adverse event / serious adverse event log.
# "site" and "symptom" fields are what the pharmacovigilance ML signal
# detector clusters on to flag unusual concentrations.
AE_REPORTS = [
    {"id": 1, "trial_id": "AIIA-CT-001", "site": "AIIA Delhi", "symptom": "Nausea", "severity": "Mild", "date": _d(-12), "serious": False, "meddra_code": "10028813", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 2, "trial_id": "AIIA-CT-001", "site": "AIIA Delhi", "symptom": "Nausea", "severity": "Mild", "date": _d(-11), "serious": False, "meddra_code": "10028813", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 3, "trial_id": "AIIA-CT-001", "site": "AIIA Delhi", "symptom": "Nausea", "severity": "Moderate", "date": _d(-9), "serious": False, "meddra_code": "10028813", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 4, "trial_id": "AIIA-CT-001", "site": "AIIA Delhi", "symptom": "Nausea", "severity": "Moderate", "date": _d(-8), "serious": False, "meddra_code": "10028813", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 5, "trial_id": "AIIA-CT-001", "site": "AIIA Delhi", "symptom": "Nausea", "severity": "Severe", "date": _d(-7), "serious": True, "meddra_code": "10028813", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 6, "trial_id": "AIIA-CT-001", "site": "NIA Jaipur", "symptom": "Headache", "severity": "Mild", "date": _d(-20), "serious": False, "meddra_code": "10019211", "whodrug_code": "ASHWAGANDHA-EXT"},
    {"id": 7, "trial_id": "AIIA-CT-002", "site": "IPGT&RA Jamnagar", "symptom": "Abdominal discomfort", "severity": "Mild", "date": _d(-30), "serious": False, "meddra_code": "10000059", "whodrug_code": "TRIPHALA-CHURNA"},
    {"id": 8, "trial_id": "AIIA-CT-002", "site": "AIIA Delhi", "symptom": "Diarrhoea", "severity": "Mild", "date": _d(-25), "serious": False, "meddra_code": "10012735", "whodrug_code": "TRIPHALA-CHURNA"},
    {"id": 9, "trial_id": "AIIA-CT-003", "site": "AIIA Delhi", "symptom": "Muscle soreness", "severity": "Mild", "date": _d(-5), "serious": False, "meddra_code": "10028411", "whodrug_code": "PANCHAKARMA-PROC"},
    {"id": 10, "trial_id": "AIIA-CT-004", "site": "AIIA Delhi", "symptom": "Dizziness", "severity": "Mild", "date": _d(-2), "serious": False, "meddra_code": "10013573", "whodrug_code": "GUGGULU-FORM"},
]

# DEMO ONLY: every account shares the password "sih2026" so the team can
# log in during a demo without juggling separate credentials. A real
# deployment issues per-user credentials/SSO and never ships a shared
# password - see auth.py for where that would plug in.
_DEMO_PASSWORD_HASH = generate_password_hash("sih2026")

USERS = {
    "investigator": {"name": "Dr. R. Sharma", "role": "Principal Investigator", "trials": ["AIIA-CT-001", "AIIA-CT-004"], "password_hash": _DEMO_PASSWORD_HASH},
    "coordinator": {"name": "S. Verma", "role": "Study Coordinator", "trials": ["AIIA-CT-001", "AIIA-CT-002", "AIIA-CT-003"], "password_hash": _DEMO_PASSWORD_HASH},
    "ethics": {"name": "Ethics Committee", "role": "Institutional Ethics Committee", "trials": "all", "password_hash": _DEMO_PASSWORD_HASH},
    "pv": {"name": "Pharmacovigilance Cell", "role": "NPvCC Pharmacovigilance", "trials": "all", "password_hash": _DEMO_PASSWORD_HASH},
    "leadership": {"name": "Director, AIIA", "role": "Institutional Leadership", "trials": "all", "password_hash": _DEMO_PASSWORD_HASH},
    "regulator": {"name": "CDSCO Observer", "role": "Read-only Regulator", "trials": "all", "password_hash": _DEMO_PASSWORD_HASH},
}

# Trial subjects - minimal SDTM DM-style demographics plus DPDP consent
# state and a simulated ABDM/ABHA health ID. `name_enc` is stored
# encrypted at rest (see security.py); only roles with a clinical need
# get it decrypted when served, everyone else gets a masked value.
SUBJECTS = [
    {"subject_id": "AIIA-CT-001-001", "trial_id": "AIIA-CT-001", "name_enc": encrypt("Patient A. Kulkarni"), "age": 34, "sex": "F", "arm": "Ashwagandha 500mg", "site": "AIIA Delhi", "abha_id": "12-3456-7890-1234", "consent_status": "Consented", "consent_date": "2026-06-02", "enrolled_date": "2026-06-03"},
    {"subject_id": "AIIA-CT-001-002", "trial_id": "AIIA-CT-001", "name_enc": encrypt("Patient V. Rao"), "age": 41, "sex": "M", "arm": "Placebo", "site": "AIIA Delhi", "abha_id": "23-4567-8901-2345", "consent_status": "Consented", "consent_date": "2026-06-05", "enrolled_date": "2026-06-06"},
    {"subject_id": "AIIA-CT-001-003", "trial_id": "AIIA-CT-001", "name_enc": encrypt("Patient S. Bose"), "age": 29, "sex": "F", "arm": "Ashwagandha 500mg", "site": "NIA Jaipur", "abha_id": "34-5678-9012-3456", "consent_status": "Withdrawn", "consent_date": "2026-06-10", "enrolled_date": "2026-06-11"},
    {"subject_id": "AIIA-CT-002-001", "trial_id": "AIIA-CT-002", "name_enc": encrypt("Patient K. Menon"), "age": 52, "sex": "M", "arm": "Triphala Churna", "site": "IPGT&RA Jamnagar", "abha_id": "45-6789-0123-4567", "consent_status": "Consented", "consent_date": "2025-12-01", "enrolled_date": "2025-12-02"},
    {"subject_id": "AIIA-CT-003-001", "trial_id": "AIIA-CT-003", "name_enc": encrypt("Patient N. Iyer"), "age": 46, "sex": "F", "arm": "Observational", "site": "AIIA Delhi", "abha_id": "56-7890-1234-5678", "consent_status": "Pending", "consent_date": None, "enrolled_date": "2026-08-20"},
]
