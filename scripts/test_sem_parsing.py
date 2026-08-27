import sys
import re

raw_sample = [
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Fourth Semester",
        "examdate": "MAY 2026",
        "resultdate": "20/06/2026",
        "class": "Pass",
        "year": "202605",
        "regno": "NNM24IS127"
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Third Semester",
        "examdate": "DECEMBER 2025",
        "resultdate": "29/01/2026",
        "class": "Pass",
        "year": "202512",
        "regno": "NNM24IS127"
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>Second Semester",
        "examdate": "MAY 2025",
        "resultdate": "25/06/2025",
        "class": "Pass",
        "year": "202505",
        "regno": "NNM24IS127"
    },
    {
        "examname": "B.Tech (Information Science & Engineering)<br>First Semester",
        "examdate": "DECEMBER 2024",
        "resultdate": "23/01/2025",
        "class": "Pass",
        "year": "202412",
        "regno": "NNM24IS127"
    }
]

for s in raw_sample:
    examno = s.get("year") or s.get("fexamno") or s.get("examno")
    clean_name = re.sub(r"<br\s*/?>", " — ", s["examname"], flags=re.IGNORECASE).strip()
    
    # extract semester number
    sem_match = re.search(r"(First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|1st|2nd|3rd|4th|5th|6th|7th|8th|\b[1-8]\b)", clean_name, re.IGNORECASE)
    ord_map = {
        "first": 1, "1st": 1, "second": 2, "2nd": 2,
        "third": 3, "3rd": 3, "fourth": 4, "4th": 4,
        "fifth": 5, "5th": 5, "sixth": 6, "6th": 6,
        "seventh": 7, "7th": 7, "eighth": 8, "8th": 8
    }
    sem_num = ord_map.get(sem_match.group(1).lower()) if sem_match else None
    
    print(f"Exam: {clean_name} | SemNum: {sem_num} | Year/ExamNo: {examno} | Result: {s['class']}")

