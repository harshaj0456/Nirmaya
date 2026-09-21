"""
AIIA CTMS - backend API (SIH prototype)

Endpoints map directly to the SIH problem statement's "Expected solution"
list: portfolio view, configurable KPIs/alerts, pharmacovigilance signal
detection, CTRI/ethics milestone tracking, an audit trail, real
authentication, DPDP consent management, e-signatures, CDISC/ADaM export,
and simulated EDC/ABDM/FHIR integration.

Run:
    pip install -r requirements.txt
    python app.py
Then open frontend/index.html in a browser (it calls http://localhost:5000).

Demo login: any username below, password "sih2026"
  investigator | coordinator | ethics | pv | leadership | regulator
"""
from functools import wraps
from datetime import datetime, date, timezone
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from mock_data import TRIALS, AE_REPORTS, USERS, SUBJECTS, TODAY
from ml_pharmacovigilance import detector
import auth
import compliance
import cdisc_export
import integrations
from security import decrypt, mask

app = Flask(__name__)
CORS(app)

# In-memory audit trail: every write is appended, never edited or deleted,
# which is the minimum shape of an ALCOA+ "immutable, time-stamped" trail.
AUDIT_LOG = []


def log_audit(action, actor, detail):
    AUDIT_LOG.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "detail": detail,
    })


def days_between(d1, d2):
    return (d1 - d2).days


def require_auth(write=False):
    """
    Real, server-enforced authentication. The frontend can no longer just
    claim a role in a query string - every protected request must carry a
    token issued by /api/login, and write actions are blocked outright for
    the read-only Regulator role, enforced here rather than trusted from
    the client.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
            role_key = auth.role_for_token(token)
            if not role_key:
                return jsonify({"error": "unauthorized - please log in"}), 401
            if write and role_key == "regulator":
                return jsonify({"error": "read-only role cannot perform this action"}), 403
            request.role_key = role_key
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# ---------------------------------------------------------------- auth ----

@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "as_of": TODAY.isoformat()})


@app.post("/api/login")
def login():
    body = request.get_json(force=True)
    token = auth.login(body.get("username", ""), body.get("password", ""))
    if not token:
        return jsonify({"error": "invalid username or password"}), 401
    user = USERS[body["username"]]
    log_audit("LOGIN", body["username"], f"{user['role']} logged in")
    return jsonify({"token": token, "role_key": body["username"], "name": user["name"], "role": user["role"]})


@app.post("/api/logout")
def logout():
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    role_key = auth.role_for_token(token)
    if role_key:
        log_audit("LOGOUT", role_key, "session ended")
    auth.logout(token)
    return jsonify({"status": "logged out"})


# -------------------------------------------------------------- trials ----

@app.get("/api/trials")
@require_auth()
def list_trials():
    user = USERS.get(request.role_key)
    if user and user["trials"] != "all":
        visible = [t for t in TRIALS if t["id"] in user["trials"]]
    else:
        visible = TRIALS
    return jsonify(visible)


@app.get("/api/trials/<trial_id>")
@require_auth()
def get_trial(trial_id):
    trial = next((t for t in TRIALS if t["id"] == trial_id), None)
    if not trial:
        return jsonify({"error": "not found"}), 404
    trial_reports = [r for r in AE_REPORTS if r["trial_id"] == trial_id]
    return jsonify({**trial, "ae_reports": trial_reports})


def compute_alerts():
    """Configurable-style alerts: enrolment lag, CTRI update due,
    ethics renewal due, overdue monitoring visit - as named explicitly
    in the problem statement's example alert list."""
    alerts = []
    for t in TRIALS:
        enrol_pct = t["current_enrollment"] / t["target_enrollment"]
        if t["status"] == "Active" and enrol_pct < 0.7:
            alerts.append({
                "trial_id": t["id"], "type": "Enrollment Lag", "severity": "warning",
                "detail": f"{t['title']} is at {enrol_pct:.0%} of target enrollment"
            })

        ctri_age = days_between(TODAY, date.fromisoformat(t["ctri_last_updated"]))
        if ctri_age > 180:
            alerts.append({
                "trial_id": t["id"], "type": "CTRI Update Overdue", "severity": "critical",
                "detail": f"CTRI record last updated {ctri_age} days ago (6-month limit exceeded)"
            })
        elif ctri_age > 150:
            alerts.append({
                "trial_id": t["id"], "type": "CTRI Update Due Soon", "severity": "warning",
                "detail": f"CTRI record last updated {ctri_age} days ago"
            })

        if t["ethics_status"] == "Renewal Due":
            alerts.append({
                "trial_id": t["id"], "type": "Ethics Approval Renewal Due", "severity": "critical",
                "detail": f"{t['title']} requires IEC re-approval"
            })

        if t["next_monitoring_visit"]:
            visit_date = date.fromisoformat(t["next_monitoring_visit"])
            days_overdue = days_between(TODAY, visit_date)
            if days_overdue > 0:
                alerts.append({
                    "trial_id": t["id"], "type": "Monitoring Visit Overdue", "severity": "critical",
                    "detail": f"Scheduled monitoring visit is {days_overdue} day(s) overdue"
                })
            elif days_overdue >= -7:
                alerts.append({
                    "trial_id": t["id"], "type": "Monitoring Visit Due Soon", "severity": "warning",
                    "detail": f"Monitoring visit scheduled in {-days_overdue} day(s)"
                })

        if t["protocol_deviations"] >= 5:
            alerts.append({
                "trial_id": t["id"], "type": "Protocol Deviation Threshold", "severity": "warning",
                "detail": f"{t['protocol_deviations']} protocol deviations logged"
            })
    return alerts


@app.get("/api/kpis")
@require_auth()
def get_kpis():
    total_trials = len(TRIALS)
    active = len([t for t in TRIALS if t["status"] in ("Active", "Enrolling")])
    total_target = sum(t["target_enrollment"] for t in TRIALS)
    total_current = sum(t["current_enrollment"] for t in TRIALS)
    open_queries = sum(t["data_query_open"] for t in TRIALS)
    sae_count = len([r for r in AE_REPORTS if r["serious"]])

    return jsonify({
        "as_of": TODAY.isoformat(),
        "total_trials": total_trials,
        "active_trials": active,
        "overall_enrollment_pct": round(total_current / total_target, 3) if total_target else 0,
        "open_data_queries": open_queries,
        "sae_count": sae_count,
        "ae_count": len(AE_REPORTS),
        "alerts": compute_alerts(),
    })


# ----------------------------------------------------------- AE reports ---

@app.get("/api/ae-reports")
@require_auth()
def get_ae_reports():
    trial_id = request.args.get("trial_id")
    reports = AE_REPORTS
    if trial_id:
        reports = [r for r in reports if r["trial_id"] == trial_id]
    return jsonify(reports)


@app.post("/api/ae-reports")
@require_auth(write=True)
def create_ae_report():
    body = request.get_json(force=True)
    required = ["trial_id", "site", "symptom", "severity", "serious"]
    missing = [f for f in required if f not in body]
    if missing:
        return jsonify({"error": f"missing fields: {missing}"}), 400

    new_id = max((r["id"] for r in AE_REPORTS), default=0) + 1
    report = {
        "id": new_id,
        "trial_id": body["trial_id"],
        "site": body["site"],
        "symptom": body["symptom"],
        "severity": body["severity"],
        "date": body.get("date", TODAY.isoformat()),
        "serious": bool(body["serious"]),
        "meddra_code": body.get("meddra_code", "UNCODED"),
        "whodrug_code": body.get("whodrug_code", "UNCODED"),
    }
    AE_REPORTS.append(report)
    log_audit(
        action="AE_REPORT_CREATED",
        actor=request.role_key,
        detail=f"{report['symptom']} ({report['severity']}) logged for {report['trial_id']} at {report['site']}"
    )
    return jsonify(report), 201


@app.get("/api/pharmacovigilance/signals")
@require_auth()
def get_signals():
    """
    Runs the IsolationForest-based signal detector over current AE data.
    This is the NPvCC-facing endpoint: it feeds aggregate safety signals
    to the DSMB / institutional leadership view.
    """
    signals = detector.detect(AE_REPORTS)
    return jsonify(signals)


@app.get("/api/audit-log")
@require_auth()
def get_audit_log():
    return jsonify(AUDIT_LOG)


@app.get("/api/fhir/AdverseEvent")
@require_auth()
def fhir_adverse_events():
    """
    Minimal illustrative HL7 FHIR R4-shaped export of AE data, to
    demonstrate the interoperability requirement. A production system
    would use a proper FHIR server/library (e.g. fhir.resources); this
    hand-built Bundle is enough to show the mapping in a demo.
    """
    entries = []
    for r in AE_REPORTS:
        entries.append({
            "resource": {
                "resourceType": "AdverseEvent",
                "id": str(r["id"]),
                "actuality": "actual",
                "event": {
                    "coding": [{
                        "system": "http://terminology.hl7.org/CodeSystem/meddra",
                        "code": r["meddra_code"],
                        "display": r["symptom"],
                    }]
                },
                "subject": {"reference": f"Study/{r['trial_id']}"},
                "date": r["date"],
                "seriousness": {
                    "coding": [{"code": "SAE" if r["serious"] else "AE"}]
                },
                "suspectEntity": [{
                    "instance": {"display": r["whodrug_code"]}
                }],
            }
        })
    return jsonify({"resourceType": "Bundle", "type": "collection", "entry": entries})


# ------------------------------------------------------- subjects/consent -

# Roles with a genuine clinical need to see subject identity, per
# role-based access. Everyone else gets a masked value - a concrete,
# working example of DPDP "data minimisation" rather than a slide claim.
_CAN_VIEW_SUBJECT_IDENTITY = {"investigator", "coordinator", "ethics"}


@app.get("/api/subjects")
@require_auth()
def list_subjects():
    trial_id = request.args.get("trial_id")
    subjects = SUBJECTS
    if trial_id:
        subjects = [s for s in subjects if s["trial_id"] == trial_id]

    can_view = request.role_key in _CAN_VIEW_SUBJECT_IDENTITY
    out = []
    for s in subjects:
        plain = decrypt(s["name_enc"])
        out.append({
            **{k: v for k, v in s.items() if k != "name_enc"},
            "name": plain if can_view else mask(plain),
        })
    return jsonify(out)


@app.post("/api/consent")
@require_auth(write=True)
def update_consent():
    body = request.get_json(force=True)
    for field in ("trial_id", "subject_id", "status"):
        if field not in body:
            return jsonify({"error": f"missing field: {field}"}), 400

    subject = next((s for s in SUBJECTS if s["subject_id"] == body["subject_id"]), None)
    if not subject:
        return jsonify({"error": "unknown subject"}), 404

    subject["consent_status"] = body["status"]
    if body["status"] == "Consented":
        subject["consent_date"] = body.get("date", TODAY.isoformat())

    entry = compliance.record_consent(body["trial_id"], body["subject_id"], body["status"], request.role_key)
    log_audit("CONSENT_UPDATED", request.role_key, f"{body['subject_id']} -> {body['status']}")
    return jsonify(entry), 201


@app.get("/api/consent/log")
@require_auth()
def consent_log():
    return jsonify(compliance.CONSENT_LOG)


# ------------------------------------------------------------ e-signature -

@app.post("/api/esign")
@require_auth(write=True)
def create_esignature():
    body = request.get_json(force=True)
    for field in ("meaning", "record_type", "record_id"):
        if field not in body:
            return jsonify({"error": f"missing field: {field}"}), 400

    user = USERS[request.role_key]
    entry = compliance.capture_esignature(
        actor=user["name"], role=user["role"],
        meaning=body["meaning"], record_type=body["record_type"], record_id=body["record_id"],
    )
    log_audit("ESIGNATURE_CAPTURED", request.role_key, f"{body['meaning']} on {body['record_type']} {body['record_id']}")
    return jsonify(entry), 201


@app.get("/api/esign")
@require_auth()
def list_esignatures():
    return jsonify({
        "signatures": compliance.ESIGNATURES,
        "chain_valid": compliance.verify_chain(),
    })


# -------------------------------------------------------------- compliance

@app.get("/api/compliance/posture")
@require_auth()
def compliance_posture():
    return jsonify(compliance.COMPLIANCE_POSTURE)


# ------------------------------------------------------------------ CDISC -

@app.get("/api/cdisc/sdtm/dm")
@require_auth()
def cdisc_dm():
    rows = cdisc_export.sdtm_dm_rows(SUBJECTS)
    if request.args.get("format") == "csv":
        return Response(cdisc_export.to_csv(rows), mimetype="text/csv",
                         headers={"Content-Disposition": "attachment; filename=DM.csv"})
    return jsonify(rows)


@app.get("/api/cdisc/sdtm/ae")
@require_auth()
def cdisc_ae():
    rows = cdisc_export.sdtm_ae_rows(AE_REPORTS)
    if request.args.get("format") == "csv":
        return Response(cdisc_export.to_csv(rows), mimetype="text/csv",
                         headers={"Content-Disposition": "attachment; filename=AE.csv"})
    return jsonify(rows)


@app.get("/api/cdisc/adam/adae")
@require_auth()
def cdisc_adae():
    rows = cdisc_export.adam_adae_rows(AE_REPORTS)
    if request.args.get("format") == "csv":
        return Response(cdisc_export.to_csv(rows), mimetype="text/csv",
                         headers={"Content-Disposition": "attachment; filename=ADAE.csv"})
    return jsonify(rows)


@app.get("/api/cdisc/define-xml")
@require_auth()
def cdisc_define_xml():
    xml = cdisc_export.define_xml(["DM", "AE", "ADAE"])
    return Response(xml, mimetype="application/xml",
                     headers={"Content-Disposition": "attachment; filename=define.xml"})


# -------------------------------------------------------------- integrations

@app.get("/api/integrations/status")
@require_auth()
def integrations_status():
    return jsonify(integrations.INTEGRATION_STATUS)


@app.post("/api/integrations/edc-sync")
@require_auth(write=True)
def integrations_sync():
    trial_ids = [t["id"] for t in TRIALS]
    record = integrations.simulate_edc_sync(AE_REPORTS, trial_ids)
    log_audit("EDC_SYNC", request.role_key, f"Simulated EDC sync pulled AE #{record['id']} for {record['trial_id']}")
    return jsonify(record), 201


if __name__ == "__main__":
    app.run(debug=True, port=5000)
