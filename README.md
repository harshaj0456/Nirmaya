# AIIA CTMS — SIH Problem Statement 46 Prototype

A working MVP of the real-time, cloud-based Clinical Trial Management System
and pharmacovigilance dashboard described in the problem statement, built
for the internal-round demo.

## What's included

```
aiia-ctms/
├── backend/
│   ├── app.py                    Flask REST API + auth enforcement
│   ├── auth.py                   Token-based login/session store
│   ├── compliance.py             DPDP consent log, e-signature ledger, compliance posture
│   ├── cdisc_export.py           SDTM (DM/AE) + ADaM (ADAE) rows, Define-XML
│   ├── integrations.py           Simulated EDC / ABDM / FHIR integration layer
│   ├── security.py               Fernet encryption-at-rest demo for subject identity
│   ├── ml_pharmacovigilance.py   Isolation Forest signal-detection model
│   ├── mock_data.py              Seed data (trials, AE reports, subjects, users/roles)
│   └── requirements.txt
├── frontend/
│   └── index.html                Single-file dashboard (HTML/CSS/JS), AYUSH color theme
└── README.md
```

## Demo login

Any of these usernames, password `sih2026` for all (shared demo password — flagged in code as demo-only, a real deployment issues per-user credentials):

`investigator` · `coordinator` · `ethics` · `pv` · `leadership` · `regulator`

## Running it

```bash
cd backend
pip install -r requirements.txt
python app.py
```

This starts the API at `http://localhost:5000`. Then just open
`frontend/index.html` directly in a browser (double-click it, or serve it
with `python -m http.server` from the `frontend/` folder). The dashboard
calls the API over `fetch`, so both need to be running.

## How this maps to the problem statement

| Problem statement requirement | Where it lives |
|---|---|
| Real-time portfolio view, per-study drill-down | `/api/trials`, `/api/trials/<id>`, trial table in the dashboard |
| Configurable KPIs + alerts (enrollment lag, CTRI update due, overdue visit) | `compute_alerts()` in `app.py` |
| Role-based access (PI, coordinator, Ethics Committee, PV, admin, regulator) | `mock_data.USERS`, role switcher in the sidebar, `applyRoleVisibility()` |
| Pharmacovigilance module (AE/SAE capture, MedDRA/WHODrug coding, signal detection) | `ml_pharmacovigilance.py`, `/api/ae-reports`, `/api/pharmacovigilance/signals` |
| CTRI + ethics milestone tracking | `ctri_last_updated`, `ethics_status` fields, 6-month-overdue alert logic |
| Immutable, time-stamped audit trail (ALCOA+) | `AUDIT_LOG` (append-only) + `/api/audit-log` |
| HL7 FHIR R4 interoperability | `/api/fhir/AdverseEvent` — illustrative FHIR Bundle export |
| Tailored dashboards per role | Sidebar nav + role-gated forms change per logged-in role |
| Strictly role-based access | `require_auth()` decorator — 401 with no token, 403 on write for Regulator, enforced server-side not just hidden in UI |
| CDISC-aligned data models (CDASH/SDTM/ADaM) | `cdisc_export.py` — SDTM DM/AE rows, ADaM ADAE rows |
| Submission-ready dataset export (SDTM/ADaM, Define-XML) | `/api/cdisc/sdtm/dm`, `/sdtm/ae`, `/adam/adae` (CSV), `/define-xml` |
| Informed-consent and DPDP privacy controls | `/api/consent` (append-only consent log), `/api/subjects` (masked identity for roles without clinical need) |
| Electronic-signature controls | `/api/esign` — hash-chained, tamper-evident signature ledger |
| Real EDC/ABDM integration | `integrations.py` + `/api/integrations/status`, `/edc-sync` — simulated but real integration shape |
| Encryption / secure hosting | `security.py` (Fernet encryption-at-rest demo) + `/api/compliance/posture` (hosting/ISO 27001/CERT-In posture, honestly labeled as simulated) |
| Real authentication | `/api/login`, `/api/logout`, token required on every protected endpoint |

## The ML model, in plain terms

`ml_pharmacovigilance.py` groups adverse-event reports by (trial, symptom)
and engineers four features per cluster: report count, number of distinct
sites, days between first and last report, and average severity. An
`IsolationForest` is trained on a synthetic baseline of "ordinary" AE
clustering behaviour (low count, spread out, mostly mild), so it learns
what unremarkable reporting looks like and can flag clusters that deviate
from it.

Every flagged signal ships with a plain-language reason (e.g. *"5 reports
of 'Nausea' within 5 days"*) rather than just a score, because
pharmacovigilance decisions need to be auditable — a black-box number
alone isn't enough evidence for a Data Safety Monitoring Board. A single
Serious Adverse Event always escalates regardless of the ML score, since
safety rules should never be silently overridden by a statistical model.

In the seed data, this correctly identifies the Ashwagandha trial's
5-report nausea cluster (including one SAE) as a signal, while leaving
routine single-report entries alone.

## Extending for the later staged phases

The problem statement explicitly allows a staged build:

1. **This MVP** — core study tracking, KPIs, alerts, pharmacovigilance
   signal detection, audit trail, role-based views.
2. **Next** — real EDC integration, a proper FHIR server (e.g.
   `fhir.resources` or HAPI FHIR) instead of the hand-built Bundle, and
   ABDM building-block hooks.
3. **After that** — full CDISC submission export (SDTM/ADaM datasets,
   Define-XML) and advanced analytics on top of the KPI data already being
   collected.

Swap `mock_data.py` for a real database (Postgres, with an append-only
audit table) when moving past the prototype stage — the API layer above it
doesn't need to change shape.
