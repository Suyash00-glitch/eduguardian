"""
EduGuardian Student Portal Adapter
====================================
Authoritative University Solutions Student Portal Integration
Base URL: https://studentportal.universitysolutions.in

CONFIRMED PORTAL API CONTRACT:
  AUTH:
    POST /signin.php
    Body: regno=<mobile>&passwd=<password>
    Response: { "status": "success", "error_code": 0, "msg": "..." }
    Sets session cookie (PHPSESSID)

  PROFILE:
    POST /src/profile.php (with session cookie)
    Response JSON:
      status: "success"
      fname: "MOHAMMED AJMAL"
      strRegno: "NNM24IS127"
      strMobile: "9110241337"
      strEmail: "nnm24is127@nmamit.in"
      college: "1001 - NMAM Institute of Technology, Nitte"
      fdegree: "BTIS24"
      degree: "B.Tech (Information Science & Engineering)"
      fcollcode: "1001"
      funivcode: "049"
      ffatname: "ABDUL RAHIMAN"
      strParentMob: "9945936732"

  ATTENDANCE:
    GET /app.php?a=viewAttendanceDetsummary&univcode=<univcode>&date=YYYY-MM-DD

  RESULTS SUMMARY:
    GET /src/results_new.php?a=getResAll&UNIVCODE=<univcode>&REGNO=<regno>
    (also works without query parameters if session is valid)
    Returns array of semester records:
      examname: "B.Tech (Information Science & Engineering)<br>Fourth Semester"
      examdate: "MAY 2026"
      resultdate: "20/06/2026"
      class: "Pass"
      year: "202605"  <-- THIS IS THE EXAM IDENTIFIER PASSED TO getResults!
      regno: "NNM24IS127"
      sgpa: "8.42" (if available)
      cgpa: "8.15" (if available)

  MARKS CARD / DETAILED RESULTS (per semester):
    GET /src/results_new.php?a=getResults&examno=<year>&regno=<regno>
    Response JSON:
      error_code: 0
      studDet: { FSGPA: "8.42", FCGPA: "8.15", FRESULT: "Pass", FEXAMNAME: "...", FDESCPN: "..." }
      body: [
        {
          sl_no: 1,
          fsubcode: "22IS41",
          subject: "Database Management Systems",
          ia_exam: "45",
          uni_exam: "48",
          thtot: "93",
          FMAXMARKS: "100",
          FGRADE: "O",
          FGP: "10",
          FCREDITS: "4",
          result: "Pass",
          FSGPA: "8.42",
          FCGPA: "8.15"
        },
        ...
      ]

SECURITY:
  - Passwords are NEVER stored in PostgreSQL, logs, StudentContext, or sent to LLMs.
  - Passwords exist solely in ephemeral memory during authentication.
  - Guardian fields (father/mother name, mobile) are EXCLUDED from AI-facing identity.
  - Student isolation guaranteed by session-scoped HTTP openers.
"""

import urllib.request
import urllib.parse
import ssl
import http.cookiejar
import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List

logger = logging.getLogger("portal_adapter")

PORTAL_BASE_URL      = "https://studentportal.universitysolutions.in"
SIGNIN_ENDPOINT      = f"{PORTAL_BASE_URL}/signin.php"
PROFILE_ENDPOINT     = f"{PORTAL_BASE_URL}/src/profile.php"
APP_ENDPOINT         = f"{PORTAL_BASE_URL}/app.php"
RESULTS_ENDPOINT     = f"{PORTAL_BASE_URL}/src/results_new.php"
OLD_RESULTS_ENDPOINT = f"{PORTAL_BASE_URL}/src/old_results.php"


def _create_ssl_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _make_opener(cookie_jar: http.cookiejar.CookieJar) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        urllib.request.HTTPSHandler(context=_create_ssl_context())
    )


def _default_headers(referer: str = f"{PORTAL_BASE_URL}/MainPage.html") -> dict:
    return {
        "User-Agent":       "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer":          referer,
        "Accept":           "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
    }


def _pick(d: dict, *keys: str) -> Optional[str]:
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if v is not None and str(v).strip() and str(v).strip().lower() not in ("null", "none", "", "-"):
            return str(v).strip()
    return None


def _pick_float(d: dict, *keys: str) -> Optional[float]:
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if v is not None:
            try:
                val = str(v).strip()
                if val not in ("-", "null", "none", "", "na", "n/a"):
                    return float(val)
            except (ValueError, TypeError):
                pass
    return None


def authenticate_portal(
    mobile: str,
    password: str,
    captcha: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[Dict[str, str]]]:
    clean_mobile   = str(mobile).strip().replace(" ", "").replace("'", "").replace('"', "").replace("&", "")
    clean_password = str(password).strip().replace("'", "").replace('"', "").replace("&", "")

    if len(clean_mobile) != 10 or not clean_mobile.isdigit():
        return False, "Student mobile number must be exactly 10 digits.", None
    if not clean_password:
        return False, "Student Portal password is required.", None

    jar = http.cookiejar.CookieJar()
    opener = _make_opener(jar)

    payload = {"regno": clean_mobile, "passwd": clean_password}
    if captcha:
        payload["ent_captcha"] = str(captcha).strip()

    data_bytes = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        SIGNIN_ENDPOINT, data=data_bytes,
        headers={
            **_default_headers(f"{PORTAL_BASE_URL}/index.html"),
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": PORTAL_BASE_URL,
        }
    )
    try:
        with opener.open(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="ignore").strip()
            try:
                rj = json.loads(body)
            except Exception:
                rj = {"error_code": -1, "msg": body[:200]}
            ec  = str(rj.get("error_code", "-1"))
            msg = rj.get("msg", "Authentication failed.")
            status_val = str(rj.get("status", "")).lower()

            if ec == "0" or status_val == "success" or "success" in msg.lower():
                cookies = {c.name: c.value for c in jar}
                logger.info("[PORTAL AUTH] Authentication successful. %d session cookie(s).", len(cookies))
                return True, clean_mobile, cookies
            return False, msg or "Invalid credentials.", None
    except Exception as exc:
        logger.warning("[PORTAL AUTH] Error: %s", type(exc).__name__)
        return False, f"Portal connection error: {str(exc)[:80]}", None


def _build_opener_from_cookies(cookies: Dict[str, str]) -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    for name, val in cookies.items():
        c = http.cookiejar.Cookie(
            version=0, name=name, value=val, port=None, port_specified=False,
            domain="studentportal.universitysolutions.in", domain_specified=True,
            domain_initial_dot=False, path="/", path_specified=True, secure=True,
            expires=None, discard=True, comment=None, comment_url=None, rest={}, rfc2109=False
        )
        jar.set_cookie(c)
    return _make_opener(jar)


def _do_post(opener, url: str, params: dict = None, timeout: int = 15) -> Tuple[int, str]:
    body = urllib.parse.urlencode(params or {}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        **_default_headers(),
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore")
    except Exception as ex:
        return 0, str(ex)


def _do_get(opener, url: str, timeout: int = 15) -> Tuple[int, str]:
    req = urllib.request.Request(url, headers=_default_headers())
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore")
    except Exception as ex:
        return 0, str(ex)


def _json_safe(raw: str) -> Optional[dict]:
    try:
        return json.loads(raw.strip())
    except Exception:
        return None


def _parse_profile_response(raw: str) -> Dict[str, Any]:
    stripped = raw.strip()
    parsed = _json_safe(stripped)

    if parsed is not None and isinstance(parsed, dict):
        status_str = str(parsed.get("status", "")).lower()
        error_code = str(parsed.get("error_code", ""))

        if status_str == "success" or error_code == "0" or "fname" in parsed or "strRegno" in parsed:
            data = parsed.get("data")
            if isinstance(data, dict) and len(data) >= 3:
                return data
            return parsed
        return parsed

    if "<html" in stripped.lower() or "<tr" in stripped.lower() or "<table" in stripped.lower():
        return _parse_profile_html(stripped)

    return {}


def _parse_profile_html(html: str) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|&amp;", " ", text)
    text = re.sub(r"\s+", " ", text)

    patterns = [
        (r"Student\s+Name\s*[:\-]\s*([A-Z][A-Z\s.]{2,60})",        "fname"),
        (r"Register\s+[Nn]umber\s*[:\-]\s*([A-Z0-9]{4,20})",      "strRegno"),
        (r"Mobile\s+[Nn]umber\s*[:\-]\s*(\d{10,12})",              "strMobile"),
        (r"Email\s+Id\s*[:\-]\s*([\w.\-]+@[\w.\-]+\.\w+)",         "strEmail"),
        (r"College[/\s]+Department\s*[:\-]\s*([^:\r\n]{5,120}?)",  "college"),
        (r"Department\s*[:\-]\s*([^:\r\n]{3,80})",                 "degree"),
        (r"Degree\s*[:\-]\s*([^:\r\n]{2,40})",                     "fdegree"),
    ]

    for pattern, field in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            if val and field not in result:
                result[field] = val

    return result


def fetch_portal_student_data(
    mobile: str,
    cookies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    if not cookies:
        logger.error("[PORTAL FETCH] No session cookies. Cannot fetch portal data.")
        return normalize_student_context(
            mobile=mobile, profile={}, subjects=[], attendance=None,
            ia_marks=None, historical=[], data_source="student_portal"
        )

    opener = _build_opener_from_cookies(cookies)
    today  = datetime.now().strftime("%Y-%m-%d")

    # 1. Profile Extraction
    status, profile_raw = _do_post(opener, PROFILE_ENDPOINT, {})
    logger.info("[PORTAL FETCH] POST /src/profile.php -> HTTP %s (%d bytes)", status, len(profile_raw))
    raw_profile = _parse_profile_response(profile_raw)

    real_usn = _pick(raw_profile, "strRegno", "strregno", "fregno", "FREGNO", "regno", "REGNO")
    real_name = _pick(raw_profile, "fname", "FNAME", "name", "NAME")
    univcode = _pick(raw_profile, "funivcode", "FUNIVCODE", "UNIVCODE", "univcode") or "049"

    logger.info(
        "[PORTAL FETCH] Profile extracted: name='%s' usn='%s' univcode='%s'",
        real_name, real_usn, univcode
    )

    # 2. Attendance
    att_url = f"{APP_ENDPOINT}?a=viewAttendanceDetsummary&univcode={univcode}"
    att_status, att_raw = _do_get(opener, att_url)
    raw_attendance = None
    att_parsed = _json_safe(att_raw)
    if att_parsed and str(att_parsed.get("error_code")) == "0" and att_parsed.get("data"):
        raw_attendance = att_parsed["data"]
        logger.info("[PORTAL FETCH] Attendance data returned by portal.")
    else:
        logger.info("[PORTAL FETCH] Attendance not available for current semester.")

    # 3. Historical Results Summary
    regno_param = real_usn or ""
    res_url = f"{RESULTS_ENDPOINT}?a=getResAll&UNIVCODE={univcode}&REGNO={regno_param}" if regno_param else f"{RESULTS_ENDPOINT}?a=getResAll"
    res_status, res_raw = _do_get(opener, res_url)
    logger.info("[PORTAL FETCH] GET results_new.php?a=getResAll -> HTTP %s (%d bytes)", res_status, len(res_raw))

    raw_historical: List[Dict[str, Any]] = []
    res_parsed = _json_safe(res_raw)

    if res_parsed and str(res_parsed.get("error_code")) == "0" and isinstance(res_parsed.get("data"), list):
        raw_historical = res_parsed["data"]
        logger.info("[PORTAL FETCH] %d semester records found in results_new.php.", len(raw_historical))
    else:
        old_res_url = f"{OLD_RESULTS_ENDPOINT}?a=getOldResults&univcode={univcode}"
        _, old_raw = _do_get(opener, old_res_url)
        old_parsed = _json_safe(old_raw)
        if old_parsed and str(old_parsed.get("error_code")) == "0" and isinstance(old_parsed.get("data"), list):
            raw_historical = old_parsed["data"]
            logger.info("[PORTAL FETCH] %d semester records found in old_results.php.", len(raw_historical))

    # 4. Detailed Marks Card for each Historical Semester
    detailed_history: List[Dict[str, Any]] = []
    for sem in raw_historical:
        # Check all possible exam identifier keys: year, fexamno, examno
        examno = (
            sem.get("year") or sem.get("YEAR") or
            sem.get("fexamno") or sem.get("FEXAMNO") or
            sem.get("examno") or sem.get("EXAMNO")
        )

        subj_results = []
        sem_sgpa = _pick_float(sem, "sgpa", "SGPA", "fsgpa", "FSGPA")
        sem_cgpa = _pick_float(sem, "cgpa", "CGPA", "fcgpa", "FCGPA")
        sem_result = _pick(sem, "class", "CLASS", "fresult", "FRESULT", "result", "RESULT", "remarks")
        sem_examname = _pick(sem, "examname", "EXAMNAME", "fexamname", "FEXAMNAME")
        sem_examdate = _pick(sem, "examdate", "EXAMDATE")
        sem_resdate  = _pick(sem, "resultdate", "RESULTDATE", "fresdate", "FRESDATE")

        if examno:
            # 4a. Call results_new.php?a=getResults (Primary Marks Card endpoint)
            get_res_url = f"{RESULTS_ENDPOINT}?a=getResults&examno={examno}&regno={regno_param}"
            _, get_res_raw = _do_get(opener, get_res_url, timeout=12)
            get_res_p = _json_safe(get_res_raw)

            if get_res_p and str(get_res_p.get("error_code")) == "0":
                body_data = get_res_p.get("body") or get_res_p.get("data")
                if isinstance(body_data, list) and body_data:
                    subj_results = body_data
                stud_det = get_res_p.get("studDet", {})
                if isinstance(stud_det, dict):
                    if sem_sgpa is None:
                        sem_sgpa = _pick_float(stud_det, "FSGPA", "fsgpa", "SGPA", "sgpa")
                    if sem_cgpa is None:
                        sem_cgpa = _pick_float(stud_det, "FCGPA", "fcgpa", "CGPA", "cgpa")
                    if not sem_result:
                        sem_result = _pick(stud_det, "FRESULT", "fresult", "RESULT", "result")
                    if not sem_examname:
                        sem_examname = _pick(stud_det, "FEXAMNAME", "fexamname", "FDESCPN")

            # 4b. Fallback: Check if any body record has FSGPA / FCGPA
            if subj_results and isinstance(subj_results, list):
                for b_item in subj_results:
                    if isinstance(b_item, dict):
                        if sem_sgpa is None:
                            sem_sgpa = _pick_float(b_item, "FSGPA", "fsgpa", "SGPA", "sgpa")
                        if sem_cgpa is None:
                            sem_cgpa = _pick_float(b_item, "FCGPA", "fcgpa", "CGPA", "cgpa")
                        if sem_sgpa is not None and sem_cgpa is not None:
                            break

            # 4c. Fallback: Call results_new.php?a=getResDet if body was empty
            if not subj_results:
                det_url = f"{RESULTS_ENDPOINT}?a=getResDet&examno={examno}&regno={regno_param}"
                _, det_raw = _do_get(opener, det_url, timeout=12)
                det_p = _json_safe(det_raw)
                if det_p and str(det_p.get("error_code")) == "0":
                    data_field = det_p.get("data") or det_p.get("body")
                    if isinstance(data_field, list) and data_field:
                        subj_results = data_field

            # 4d. Fallback: Call old_results.php?a=getResults if still empty
            if not subj_results:
                old_det_url = f"{OLD_RESULTS_ENDPOINT}?a=getResults&examno={examno}"
                _, old_det_raw = _do_get(opener, old_det_url, timeout=12)
                old_det_p = _json_safe(old_det_raw)
                if old_det_p and str(old_det_p.get("error_code")) == "0":
                    body_field = old_det_p.get("body") or old_det_p.get("data")
                    if isinstance(body_field, list) and body_field:
                        subj_results = body_field
                    stud_det = old_det_p.get("studDet", {})
                    if isinstance(stud_det, dict):
                        if sem_sgpa is None:
                            sem_sgpa = _pick_float(stud_det, "FSGPA", "fsgpa", "SGPA", "sgpa")
                        if sem_cgpa is None:
                            sem_cgpa = _pick_float(stud_det, "FCGPA", "fcgpa", "CGPA", "cgpa")

        detailed_history.append({
            **sem,
            "fexamno": examno,
            "fexamname": sem_examname,
            "fresdate": sem_resdate,
            "fexamdate": sem_examdate,
            "fsgpa": sem_sgpa,
            "fcgpa": sem_cgpa,
            "fresult": sem_result,
            "subject_results": subj_results
        })

    print(
        f"[PORTAL EXTRACTION] name='{real_name}' usn='{real_usn}' | "
        f"historical_semesters={len(raw_historical)} | "
        f"attendance={'available' if raw_attendance else 'not_available'}"
    )

    return normalize_student_context(
        mobile=mobile,
        profile=raw_profile,
        subjects=[],
        attendance=raw_attendance,
        ia_marks=None,
        historical=detailed_history,
        data_source="student_portal"
    )


def normalize_student_context(
    mobile: str,
    profile: Dict[str, Any],
    subjects: list,
    attendance: Any,
    ia_marks: Any,
    historical: list,
    data_source: str = "student_portal"
) -> Dict[str, Any]:
    usn = _pick(profile, "strRegno", "strregno", "fregno", "FREGNO", "regno", "REGNO")
    name = _pick(profile, "fname", "FNAME", "name", "NAME")
    email = _pick(profile, "strEmail", "stremail", "femail", "FEMAIL", "email")
    portal_mobile = _pick(profile, "strMobile", "strmobile", "fmob", "FMOB", "mobile") or mobile
    college = _pick(profile, "college", "fcollname", "FCOLLNAME", "fcoll", "FCOLL")
    degree_code = _pick(profile, "fdegree", "FDEGREE")
    department = _pick(profile, "degree", "fdescpn", "FDESCPN", "fdept", "FDEPT", "fbranchname")

    semester = None
    explicit_sem = _pick(profile, "fcursem", "FCURSEM", "fsem", "FSEM", "semester")
    if explicit_sem:
        try:
            semester = int(str(explicit_sem).strip())
        except (ValueError, TypeError):
            pass

    if semester is None and isinstance(historical, list) and len(historical) > 0:
        semester = len(historical) + 1

    section = _pick(profile, "fsec", "FSEC", "section", "SECTION")

    if not name and data_source == "student_portal":
        name = "Not available from Student Portal"
    if not usn and data_source == "student_portal":
        usn = "Not available from Student Portal"
    if not department and data_source == "student_portal":
        department = "Not available from Student Portal"
    if not degree_code and data_source == "student_portal":
        degree_code = "Not available from Student Portal"

    # Attendance
    attendance_data: Dict[str, Any] = {"value": None, "status": "not_available", "records": []}
    if attendance:
       records = attendance if isinstance(attendance, list) else [attendance]
    if isinstance(attendance, list) and attendance:
            def _iv(item, *ks) -> int:
                for k in ks:
                    v = item.get(k)
                    if v is not None:
                        try:
                            return int(str(v).strip() or "0")
                        except (ValueError, TypeError):
                            pass
                return 0

            held = sum(_iv(r, "conducted", "HELD", "held", "FCLSHELD", "fclsheld", "classes_held", "TOTAL") for r in records)
            attended = sum(_iv(r, "attended", "ATTENDED", "FCLSATT", "fclsatt", "classes_attended", "PRESENT") for r in records)

            # Map college portal keys to the keys the React UI is looking for
            formatted_records = []
            for r in records:
                r_held = _iv(r, "conducted", "HELD", "held", "classes_held")
                r_att = _iv(r, "attended", "ATTENDED", "attended", "classes_attended")
                pct = round((r_att / r_held * 100), 2) if r_held > 0 else 0.0
                formatted_records.append({
                    **r,
                    "subject": r.get("fsubname") or r.get("subject") or r.get("subject_name"),
                    "subject_name": r.get("fsubname") or r.get("subject") or r.get("subject_name"),
                    "subject_code": r.get("fsubcode") or r.get("subject_code"),
                    "classes_held": r_held,
                    "held": r_held,
                    "classes_attended": r_att,
                    "attended": r_att,
                    "attendance_percentage": pct,
                    "percentage": pct,
                    "status": "Safe" if pct >= 75.0 else "Attention"
                })

            if held > 0:
                attendance_data = {
                    "value": round(attended / held * 100, 2),
                    "status": "available",
                    "classes_held": held,
                    "classes_attended": attended,
                    "records": formatted_records,
                }
            else:
                attendance_data = {
                    "value": None,
                    "status": "not_available",
                    "note": "Current semester attendance records are pending faculty upload.",
                    "records": formatted_records,
                }
            def _iv(item, *ks) -> int:
                for k in ks:
                    v = item.get(k)
                    if v is not None:
                        try: return int(str(v).strip() or "0")
                        except: pass
                return 0
            held     = sum(_iv(r, "conducted", "HELD","held","FCLSHELD","fclsheld","classes_held","TOTAL") for r in records)
            attended = sum(_iv(r, "ATTENDED","attended","FCLSATT","fclsatt","classes_attended","PRESENT") for r in records)
            if held > 0:
                attendance_data = {
                    "value": round(attended / held * 100, 2),
                    "status": "available",
                    "classes_held": held,
                    "classes_attended": attended,
                    "records": records,
                }
            else:
                attendance_data = {
                    "value": None,
                    "status": "not_available",
                    "note": "Current semester attendance records are pending faculty upload.",
                    "records": records,
                }
    elif isinstance(attendance, dict):
            pv = _pick_float(attendance, "PERCENTAGE","percentage","FPERCENTAGE","fpercentage")
            if pv is not None:
                attendance_data = {"value": pv, "status": "available", "records": [attendance]}

    assessments_data: Dict[str, Any] = {"value": None, "status": "not_available", "records": []}
    assignments_data: Dict[str, Any] = {"value": None, "status": "not_available", "missed_count": 0, "records": []}
    lms_data:         Dict[str, Any] = {"value": None, "status": "not_available", "study_minutes": 0}

    # Historical Semester Results & Marks Card Parsing
    normalized_history = []
    all_sgpas: List[Tuple[int, float]] = []
    all_cgpas: List[Tuple[int, float]] = []
    latest_cgpa: Optional[float] = None
    total_credits_earned = 0.0
    arrears_count = 0
    failed_subjects_history = []
    semesters_dict: Dict[str, Any] = {}

    for idx, item in enumerate(historical or []):
        if not isinstance(item, dict):
            continue

        raw_exam_name = _pick(item, "examname", "EXAMNAME", "fexamname", "FEXAMNAME", "FRESEXAMDATE") or ""
        # Clean literal <br> tags from examname
        clean_exam_name = re.sub(r"<br\s*/?>", " — ", raw_exam_name, flags=re.IGNORECASE).strip()

        res_date  = _pick(item, "resultdate", "RESULTDATE", "fresdate", "FRESDATE")
        exam_date = _pick(item, "examdate", "EXAMDATE", "FRESEXAMDATE")
        sem_id    = _pick(item, "year", "YEAR", "fexamno", "FEXAMNO", "examno", "EXAMNO", "fsem", "semester") or str(idx + 1)
        sgpa      = _pick_float(item, "sgpa", "SGPA", "fsgpa", "FSGPA")
        cgpa      = _pick_float(item, "cgpa", "CGPA", "fcgpa", "FCGPA")
        result    = _pick(item, "class", "CLASS", "fresult", "FRESULT", "result", "RESULT", "remarks", "status")

        # Derive semester number (1 to 8)
        sem_num = None
        if clean_exam_name:
            sem_match = re.search(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|1st|2nd|3rd|4th|5th|6th|7th|8th| [1-8] )", clean_exam_name, re.IGNORECASE)
            if sem_match:
                ord_map = {
                    "first": 1, "1st": 1, "second": 2, "2nd": 2,
                    "third": 3, "3rd": 3, "fourth": 4, "4th": 4,
                    "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
                    "seventh": 7, "7th": 7, "eighth": 8, "8th": 8
                }
                w = sem_match.group(1).lower()
                sem_num = ord_map.get(w, int(w) if w.isdigit() else None)

        if sem_num is None:
            sem_num = len(historical) - idx if len(historical) >= idx else idx + 1

        if sem_num and sgpa is not None:
            all_sgpas.append((sem_num, sgpa))
        if sem_num and cgpa is not None:
            all_cgpas.append((sem_num, cgpa))

        # Parse detailed subject marks
        raw_subj_list = item.get("subject_results") or item.get("res") or item.get("results") or []
        parsed_subjects = []
        sem_credits = 0.0
        sem_marks_secured = 0.0
        sem_max_marks = 0.0

        for s in raw_subj_list:
            if not isinstance(s, dict):
                continue
            sub_code  = _pick(s, "fsubcode", "FSUBCODE", "SUBCODE", "subcode", "code")
            sub_name  = _pick(s, "subject", "fsubname", "FSUBNAME", "SUBNAME", "subname", "name")
            int_marks = _pick_float(s, "ia_exam", "fintmarks", "FTHINT", "fthint", "INTMARKS", "ia")
            ext_marks = _pick_float(s, "uni_exam", "fextmarks", "FTHEXT", "fthext", "EXTMARKS", "external")
            tot_marks = _pick_float(s, "thtot", "FTOTMARKS", "ftotmarks", "mthprue", "MARKS", "marks", "totmarks")
            max_m     = _pick_float(s, "FMAXMARKS", "fmaxmarks", "fsmaxmarks", "MAXMARKS", "max_marks", "MAX")
            grade     = _pick(s, "FGRADE", "fgrade", "GRADE", "grade")
            gp        = _pick_float(s, "FGP", "fgp", "FGRADEPOINT", "gradepoint")
            credits_v = _pick_float(s, "FCREDITS", "fcredits", "CREDITS", "credits")
            sub_res   = _pick(s, "result", "remarks", "RESULT", "FRESULT", "fresult", "status")

            if credits_v:
                sem_credits += credits_v
                total_credits_earned += credits_v
            if tot_marks:
                sem_marks_secured += tot_marks
            if max_m:
                sem_max_marks += max_m

            is_fail = False
            if sub_res and sub_res.upper() in ("FAIL", "F", "ARREAR", "WITHHELD", "AB"):
                is_fail = True
            elif grade and grade.upper() in ("F", "AB", "FAIL"):
                is_fail = True

            if is_fail:
                arrears_count += 1
                failed_subjects_history.append({
                    "semester": str(sem_num),
                    "subject_code": sub_code,
                    "subject_name": sub_name,
                    "grade": grade,
                    "result": sub_res
                })

            parsed_subjects.append({
                "subject_code":   sub_code,
                "subject_name":   sub_name,
                "internal_marks": int_marks,
                "external_marks": ext_marks,
                "marks_obtained": tot_marks,
                "max_marks":      max_m,
                "grade":          grade,
                "grade_point":    gp,
                "credits":        credits_v,
                "result":         sub_res or ("PASS" if not is_fail else "FAIL"),
            })

        display_sem_label = str(sem_num) if sem_num else str(sem_id)

        sem_record = {
            "semester":        display_sem_label,
            "semester_number": sem_num,
            "exam_name":       clean_exam_name or f"Semester {display_sem_label} Examination",
            "exam_date":       exam_date,
            "result_date":     res_date,
            "sgpa":            sgpa,
            "cgpa":            cgpa,
            "result":          result or "Pass",
            "credits":         sem_credits if sem_credits > 0 else None,
            "marks_secured":   sem_marks_secured if sem_marks_secured > 0 else None,
            "max_marks":       sem_max_marks if sem_max_marks > 0 else None,
            "subject_results": parsed_subjects,
        }
        normalized_history.append(sem_record)
        semesters_dict[display_sem_label] = sem_record

    # Sort descending by semester_number (Semester 4, 3, 2, 1)
    normalized_history.sort(key=lambda x: x.get("semester_number") or 0, reverse=True)

    # Calculate SGPA Trend & Latest CGPA
    sgpa_trend = "insufficient_data"
    latest_sgpa = None
    if len(all_sgpas) >= 2:
        all_sgpas.sort(key=lambda x: x[0])
        latest_sgpa = all_sgpas[-1][1]
        prev_sgpa   = all_sgpas[-2][1]
        diff = latest_sgpa - prev_sgpa
        if diff >= 0.25:
            sgpa_trend = "improving"
        elif diff <= -0.25:
            sgpa_trend = "declining"
        else:
            sgpa_trend = "stable"
    elif len(all_sgpas) == 1:
        latest_sgpa = all_sgpas[0][1]
        sgpa_trend = "stable"

    latest_cgpa = None
    if all_cgpas:
        all_cgpas.sort(key=lambda x: x[0])
        latest_cgpa = all_cgpas[-1][1]

    academic_performance = {
        "latest_sgpa": latest_sgpa,
        "cgpa": latest_cgpa,
        "sgpa_trend": sgpa_trend,
        "total_semesters_completed": len(normalized_history),
        "total_credits_earned": round(total_credits_earned, 1) if total_credits_earned > 0 else None,
        "arrears_count": arrears_count,
        "failed_subjects_history": failed_subjects_history,
        "semesters": semesters_dict,
    }

    return {
        "identity": {
            "student_id":   str(usn),
            "usn":          str(usn),
            "name":         name,
            "degree":       degree_code,
            "department":   department,
            "semester":     semester,
            "section":      section,
            "email":        email,
            "mobile":       portal_mobile,
            "college":      college,
        },
        "current_academic_profile": {
            "semester":          semester,
            "enrolled_subjects": subjects or [],
        },
        "attendance":          attendance_data,
        "current_assessments": assessments_data,
        "assignments":         assignments_data,
        "lms_engagement":      lms_data,
        "historical_semesters": normalized_history,
        "historical_academic_performance": academic_performance,
        "data_availability": {
            "attendance":         attendance_data["status"] == "available",
            "assessments":        False,
            "assignments":        False,
            "lms":                False,
            "historical_results": len(normalized_history) > 0,
            "marks_card":         any(len(s.get("subject_results", [])) > 0 for s in normalized_history),
        },
        "data_source": data_source,
    }
