"""
Pharmacovigilance signal-detection model.

Purpose (maps directly to the SIH problem statement's pharmacovigilance
module requirement): watch incoming Adverse Event / Serious Adverse Event
reports and flag clusters that look statistically unusual BEFORE a human
happens to notice the pattern manually - the exact gap that delayed
recognition of AYUSH-64's safety profile.

Approach for the MVP:
1. Group AE reports by (trial_id, symptom) - a "signal candidate".
2. Engineer a small feature vector per candidate: report count, number of
   distinct sites reporting it, days between first and last report
   (a fast cluster is more concerning than a slow trickle), and an average
   severity score.
3. Train an IsolationForest on a synthetic baseline of "normal" reporting
   patterns (low count, spread out, low severity) so it learns what
   unremarkable AE activity looks like.
4. Score real clusters against that baseline. Anything the model calls an
   outlier - AND that also fails a plain-language safety rule (e.g. 3+
   reports of the same symptom within 14 days, or any single SAE) - is
   surfaced as a signal that should route to the Data Safety Monitoring
   Board (DSMB), per the problem statement's escalation requirement.

This is intentionally a simple, explainable model: pharmacovigilance
decisions need to be auditable (ALCOA+), so a black-box score alone is not
enough - every flagged signal includes the plain-language reason.
"""
from datetime import datetime
from collections import defaultdict
import numpy as np
from sklearn.ensemble import IsolationForest

SEVERITY_SCORE = {"Mild": 1, "Moderate": 2, "Severe": 3}


def _parse(d):
    return datetime.fromisoformat(d)


def _synthetic_baseline(n=300, seed=42):
    """
    Synthetic 'normal' AE clusters: low count, reports spread over weeks,
    mostly mild. This stands in for a hospital's historical AE database,
    which is what a production version would train on instead.
    """
    rng = np.random.default_rng(seed)
    count = rng.poisson(1.4, n) + 1                      # usually 1-3 reports
    distinct_sites = rng.integers(1, 3, n)                # usually 1 site
    span_days = rng.integers(5, 60, n)                    # spread out
    avg_severity = rng.normal(1.3, 0.3, n).clip(1, 3)     # mostly mild
    return np.column_stack([count, distinct_sites, span_days, avg_severity])


class PharmacovigilanceSignalDetector:
    def __init__(self):
        baseline = _synthetic_baseline()
        self.model = IsolationForest(
            n_estimators=200, contamination=0.08, random_state=42
        )
        self.model.fit(baseline)

    def _cluster_candidates(self, ae_reports):
        clusters = defaultdict(list)
        for r in ae_reports:
            clusters[(r["trial_id"], r["symptom"])].append(r)
        return clusters

    def _features(self, reports):
        dates = sorted(_parse(r["date"]) for r in reports)
        span_days = max((dates[-1] - dates[0]).days, 1) if len(dates) > 1 else 1
        distinct_sites = len({r["site"] for r in reports})
        avg_severity = np.mean([SEVERITY_SCORE.get(r["severity"], 1) for r in reports])
        return [len(reports), distinct_sites, span_days, avg_severity]

    def detect(self, ae_reports):
        """
        Returns a list of signal dicts, most concerning first. Each includes
        an explicit, human-readable reason - required so a PV reviewer can
        audit why the model flagged it (ALCOA+ / GCP auditability).
        """
        clusters = self._cluster_candidates(ae_reports)
        signals = []

        for (trial_id, symptom), reports in clusters.items():
            features = self._features(reports)
            count, distinct_sites, span_days, avg_severity = features
            anomaly_score = -self.model.decision_function([features])[0]
            is_ml_outlier = self.model.predict([features])[0] == -1
            has_sae = any(r["serious"] for r in reports)

            reasons = []
            if count >= 3 and span_days <= 14:
                reasons.append(f"{count} reports of '{symptom}' within {span_days} days")
            if distinct_sites >= 2:
                reasons.append(f"reported across {distinct_sites} sites")
            if has_sae:
                reasons.append("includes at least one Serious Adverse Event")
            if avg_severity >= 2.2:
                reasons.append("average severity trending moderate-to-severe")

            # Escalate if a hard safety rule is tripped (a single SAE must
            # never be suppressed just because the model considers it
            # statistically ordinary), OR if the ML model flags a cluster
            # of 2+ reports as unusual. A lone mild report with nothing
            # else attached is not treated as a signal - that matches real
            # pharmacovigilance practice, where single mild events are
            # logged but don't trigger escalation on their own.
            should_escalate = has_sae or (count >= 3 and span_days <= 14) or (is_ml_outlier and count >= 2)

            if should_escalate:
                signals.append({
                    "trial_id": trial_id,
                    "symptom": symptom,
                    "report_count": count,
                    "distinct_sites": distinct_sites,
                    "span_days": span_days,
                    "avg_severity": round(float(avg_severity), 2),
                    "contains_sae": has_sae,
                    "anomaly_score": round(float(anomaly_score), 3),
                    "reasons": reasons or ["Flagged by anomaly model as statistically unusual"],
                    "route_to": "Data Safety Monitoring Board" if has_sae else "Pharmacovigilance Cell",
                })

        signals.sort(key=lambda s: (s["contains_sae"], s["anomaly_score"]), reverse=True)
        return signals


detector = PharmacovigilanceSignalDetector()
