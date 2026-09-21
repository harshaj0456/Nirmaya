"""
CDISC-aligned dataset export: SDTM (tabulation) and ADaM (analysis)
shaped rows, plus a minimal, illustrative Define-XML.

Honest scope note: real SDTM/ADaM/Define-XML require a full controlled
terminology library and validation against the CDISC standards (Pinnacle
21 checks, etc.). This module produces correctly *shaped* domains with
the right variable names and structure, as a demonstration that the
underlying data model is CDISC-aware - not a submission-ready package.
"""
import csv
import io
from datetime import datetime, timezone

SEVERITY_NUM = {"Mild": 1, "Moderate": 2, "Severe": 3}


def sdtm_dm_rows(subjects):
    """Demographics domain (DM)."""
    return [
        {
            "STUDYID": s["trial_id"],
            "DOMAIN": "DM",
            "USUBJID": s["subject_id"],
            "AGE": s["age"],
            "AGEU": "YEARS",
            "SEX": s["sex"],
            "ARM": s.get("arm", ""),
            "SITEID": s.get("site", ""),
            "RFSTDTC": s.get("enrolled_date", ""),
        }
        for s in subjects
    ]


def sdtm_ae_rows(ae_reports):
    """Adverse events domain (AE)."""
    return [
        {
            "STUDYID": r["trial_id"],
            "DOMAIN": "AE",
            "USUBJID": f"{r['trial_id']}-{r['id']:03d}",
            "AETERM": r["symptom"],
            "AEDECOD": r["symptom"],
            "AESEV": r["severity"].upper(),
            "AESER": "Y" if r["serious"] else "N",
            "AESTDTC": r["date"],
            "AEMEDDRACODE": r.get("meddra_code", ""),
            "AEWHODRUGCODE": r.get("whodrug_code", ""),
        }
        for r in ae_reports
    ]


def adam_adae_rows(ae_reports):
    """Analysis dataset for adverse events (ADAE) - derived from SDTM AE
    with an added numeric severity for statistical analysis, per ADaM
    conventions."""
    return [
        {
            "STUDYID": r["trial_id"],
            "USUBJID": f"{r['trial_id']}-{r['id']:03d}",
            "AETERM": r["symptom"],
            "AESEVN": SEVERITY_NUM.get(r["severity"], 1),
            "SAEFL": "Y" if r["serious"] else "N",
            "ASTDT": r["date"],
        }
        for r in ae_reports
    ]


def to_csv(rows):
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def define_xml(domains):
    """
    A minimal, illustrative Define-XML skeleton (not full ODM/Define-XML
    2.0 validated output) - enough to demonstrate that dataset metadata
    is tracked alongside the data itself, which is what Define-XML exists
    for in a real regulatory submission.
    """
    now = datetime.now(timezone.utc).isoformat()
    item_groups = "\n".join(
        f'    <ItemGroupDef OID="IG.{d}" Name="{d}" Purpose="{"Tabulation" if d in ("DM", "AE") else "Analysis"}" Repeating="Yes"/>'
        for d in domains
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<ODM FileOID="AIIA.CTMS.DEFINE" CreationDateTime="{now}" ODMVersion="1.3.2"
     xmlns="http://www.cdisc.org/ns/odm/v1.3">
  <Study OID="AIIA-CTMS-PROTOTYPE">
    <GlobalVariables>
      <StudyName>AIIA CTMS Prototype</StudyName>
      <StudyDescription>Illustrative Define-XML - demonstrates dataset metadata tracking, not submission-ready output.</StudyDescription>
    </GlobalVariables>
    <MetaDataVersion OID="MDV.1" Name="AIIA CTMS Define-XML (illustrative)">
{item_groups}
    </MetaDataVersion>
  </Study>
</ODM>"""
