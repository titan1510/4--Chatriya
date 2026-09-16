import os
import re
import subprocess
import sys


def normalize_text(text):
    """แปลงข้อความให้เป็นมาตรฐาน: ตัวพิมพ์เล็ก ลบสัญลักษณ์พิเศษ และลบช่องว่างส่วนเกิน"""
    if not text:
        return ""
    text = text.lower()
    # ลบสัญลักษณ์พิเศษที่ไม่จำเป็นออก
    text = re.sub(r'[!.,:="\'\(\)]', " ", text)
    # ยุบช่องว่างที่ซ้ำซ้อน
    return " ".join(text.split())


def extract_numbers(text):
    """ดึงตัวเลขทั้งหมดออกจากข้อความผลลัพธ์ของนักเรียน"""
    if not text:
        return []
    return [float(n) for n in re.findall(r"[-+]?\d*\.\d+|\d+", text)]


def run_student_code(filename, input_data):
    """รันไฟล์ข้อสอบของนักเรียนและรับค่าผลลัพธ์"""
    target_file = filename
    if not os.path.exists(target_file) and os.path.exists(filename + ".py"):
        target_file = filename + ".py"

    if not os.path.exists(target_file):
        return None, "File Not Found"

    try:
        process = subprocess.run(
            [sys.executable, target_file],
            input=input_data,
            text=True,
            capture_output=True,
            timeout=5,
        )
        return process.stdout, process.stderr
    except subprocess.TimeoutExpired:
        return None, "Timeout (โปรแกรมทำงานวนลูปไม่จบ)"
    except Exception as e:
        return None, str(e)


# =========================================================
# เกณฑ์การตรวจแบบยืดหยุ่นแยกรายข้อ (คะแนนเต็มข้อละ 4 คะแนน)
# =========================================================


def grade_exam_1(output, stderr, test_case):
    """ข้อ 1: ทักทาย Hello, <name>"""
    name = test_case["input"].strip()
    norm_out = normalize_text(output)

    # 1. ผ่าน 100%: มีคำว่า hello/hi และมีชื่อนักเรียน
    if ("hello" in norm_out or "hi" in norm_out) and name.lower() in norm_out:
        return 1.0
    # 2. ยืดหยุ่นบางส่วน: มีชื่อนักเรียน หรือ พิมพ์คำทักทายถูก
    elif name.lower() in norm_out or "hello" in norm_out:
        return 0.5
    return 0.0


def grade_exam_2(output, stderr, test_case):
    """ข้อ 2: คำนวณราคาเน็ต (price - discount)"""
    expected_val = test_case["expected"]
    nums = extract_numbers(output)

    # 1. ผ่าน 100%: มีตัวเลขผลลัพธ์ที่ถูกต้องอยู่ใน Output
    if any(abs(n - expected_val) < 0.01 for n in nums):
        return 1.0
    # 2. ยืดหยุ่นบางส่วน: มีการรันผลลัพธ์ออกเป็นตัวเลข
    elif len(nums) > 0:
        return 0.5
    return 0.0


def grade_exam_3(output, stderr, test_case):
    """ข้อ 3: Pass / Fail (คะแนน >= 50)"""
    expected_word = test_case["expected"].lower()
    norm_out = normalize_text(output)

    # 1. ผ่าน 100%: มีคำว่า pass หรือ fail ถูกต้อง (ไม่สนตัวเล็ก/ใหญ่)
    if expected_word in norm_out:
        return 1.0
    # 2. ยืดหยุ่นบางส่วน: พิมพ์ผลลัพธ์ทักทาย/ข้อความอื่นออกมาโดยโค้ดไม่พัง
    elif "pass" in norm_out or "fail" in norm_out:
        return 0.5
    return 0.0


def grade_exam_4(output, stderr, test_case):
    """ข้อ 4: ตัดเกรด A, B, C"""
    expected_grade = test_case["expected"].lower()
    norm_out = normalize_text(output)

    # ดึงตัวอักษรเดี่ยวๆ ในผลลัพธ์
    words = norm_out.split()

    # 1. ผ่าน 100%: แสดงเกรดตรงกับโจทย์
    if expected_grade in words or norm_out == expected_grade:
        return 1.0
    # 2. ยืดหยุ่นบางส่วน: พิมพ์เกรดกลุ่ม A, B, C ออกมาได้
    elif any(g in words for g in ["a", "b", "c"]):
        return 0.5
    return 0.0


def grade_exam_5(output, stderr, test_case):
    """ข้อ 5: ซื้อสมุดเล่มละ 20 บาท (ซื้อ >= 5 เล่ม ลด 10 บาท)"""
    expected_total = test_case["expected"]
    no_discount_total = test_case["no_discount"]
    nums = extract_numbers(output)

    # 1. ผ่าน 100%: ได้ราคารวมหักส่วนลดถูกต้อง
    if any(abs(n - expected_total) < 0.01 for n in nums):
        return 1.0
    # 2. ยืดหยุ่นบางส่วน: คำนวณราคาคูณเล่มถูก แต่ลืมคิดส่วนลด 10 บาท
    elif any(abs(n - no_discount_total) < 0.01 for n in nums):
        return 0.5
    elif len(nums) > 0:
        return 0.25
    return 0.0


# =========================================================
# ชุดข้อมูลทดสอบ (Test Cases)
# =========================================================
EXAMS = {
    "Examination_1": {
        "grader": grade_exam_1,
        "cases": [
            {"input": "Somchai\n"},
            {"input": "PoY\n"},
            {"input": "John\n"},
            {"input": "Alice\n"},
        ],
    },
    "Examination_2": {
        "grader": grade_exam_2,
        "cases": [
            {"input": "100.0\n20.0\n", "expected": 80.0},
            {"input": "250.0\n50.0\n", "expected": 200.0},
            {"input": "500.0\n100.0\n", "expected": 400.0},
            {"input": "75.5\n15.5\n", "expected": 60.0},
        ],
    },
    "Examination_3": {
        "grader": grade_exam_3,
        "cases": [
            {"input": "75\n", "expected": "Pass"},
            {"input": "30\n", "expected": "Fail"},
            {"input": "50\n", "expected": "Pass"},
            {"input": "49\n", "expected": "Fail"},
        ],
    },
    "Examination_4": {
        "grader": grade_exam_4,
        "cases": [
            {"input": "85\n", "expected": "A"},
            {"input": "70\n", "expected": "B"},
            {"input": "50\n", "expected": "C"},
            {"input": "80\n", "expected": "A"},
        ],
    },
    "Examination_5": {
        "grader": grade_exam_5,
        "cases": [
            {"input": "3\n", "expected": 60, "no_discount": 60},
            {"input": "5\n", "expected": 90, "no_discount": 100},
            {"input": "10\n", "expected": 190, "no_discount": 200},
            {"input": "4\n", "expected": 80, "no_discount": 80},
        ],
    },
}

# =========================================================
# ส่วนประมวลผลและสร้าง Markdown สรุปคะแนน
# =========================================================
total_score = 0.0
summary_rows = []

for exam_name, exam_data in EXAMS.items():
    grader = exam_data["grader"]
    cases = exam_data["cases"]

    exam_score = 0.0
    passed_cases = 0

    for case in cases:
        stdout, stderr = run_student_code(exam_name, case["input"])
        if stdout is not None:
            score = grader(stdout, stderr, case)
            exam_score += score
            if score >= 1.0:
                passed_cases += 1
            elif score > 0:
                passed_cases += 0.5

    # ปรับปัดเศษคะแนนให้อยู่ในช่วง 0-4
    final_exam_score = min(4.0, round(exam_score, 1))
    total_score += final_exam_score

    # กำหนดสถานะการแสดงผล
    if final_exam_score >= 4.0:
        status = "🟢 ผ่าน"
    elif final_exam_score > 0:
        status = "🟡 ผ่านบางส่วน"
    else:
        status = "❌ ไม่ผ่าน"

    # จัดรูปแบบตัวเลขคะแนนแบบสวยงาม
    score_display = (
        f"{int(final_exam_score)}"
        if final_exam_score.is_integer()
        else f"{final_exam_score}"
    )
    passed_display = (
        f"{int(passed_cases)}"
        if isinstance(passed_cases, int)
        or (isinstance(passed_cases, float) and passed_cases.is_integer())
        else f"{passed_cases}"
    )

    summary_rows.append(
        f"| `{exam_name}` | {status} | {passed_display}/4 เคส | {score_display} / 4 |"
    )

# สร้างตาราง Markdown สรุปคะแนน
final_total_display = (
    f"{int(total_score)}" if total_score.is_integer() else f"{total_score}"
)

markdown_summary = f"""
## 📊 สรุปผลการสอบวิชาเขียนโปรแกรม

| ข้อสอบ | สถานะการตรวจ | ผ่าน Test Cases | คะแนนที่ได้ |
| :--- | :--- | :--- | :--- |
""" + "\n".join(summary_rows) + f"""

### 🎯 คะแนนรวมทั้งหมด: {final_total_display} / 20 คะแนน
"""

print(markdown_summary)

# เขียนลง GitHub Summary
github_summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
if github_summary_path:
    with open(github_summary_path, "a", encoding="utf-8") as f:
        f.write(markdown_summary)
