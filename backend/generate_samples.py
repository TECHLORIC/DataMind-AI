import random
import datetime
from pathlib import Path
import pandas as pd
import numpy as np

SAMPLES_DIR = Path(__file__).resolve().parent / "sample_datasets"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)
np.random.seed(42)

def generate_sales(n=1000):
    regions = ["North America", "Europe", "Asia-Pacific", "Latin America", "Middle East"]
    products = ["Laptop Pro", "Cloud Server", "Enterprise Suite", "Tablet Ultra", "Smart Monitor", "Security Key"]
    segments = ["Corporate", "Consumer", "Small Business", "Government"]
    base_date = datetime.date(2025, 1, 1)

    rows = []
    for i in range(n):
        dt = base_date + datetime.timedelta(days=random.randint(0, 365))
        reg = random.choice(regions)
        prod = random.choice(products)
        seg = random.choice(segments)
        qty = random.randint(1, 25)
        base_price = {"Laptop Pro": 1200, "Cloud Server": 2500, "Enterprise Suite": 4000, "Tablet Ultra": 650, "Smart Monitor": 350, "Security Key": 50}[prod]
        unit_price = round(base_price * random.uniform(0.9, 1.1), 2)
        discount = round(random.choice([0.0, 0.05, 0.1, 0.15, 0.2]), 2)
        revenue = round(qty * unit_price * (1 - discount), 2)
        profit = round(revenue * random.uniform(0.18, 0.38), 2)

        rows.append({
            "Order_ID": f"ORD-{10000 + i}",
            "Order_Date": dt.strftime("%Y-%m-%d"),
            "Region": reg,
            "Product": prod,
            "Customer_Segment": seg,
            "Quantity": qty,
            "Unit_Price": unit_price,
            "Discount_Rate": discount,
            "Revenue": revenue,
            "Profit": profit
        })
    df = pd.DataFrame(rows)
    df.to_csv(SAMPLES_DIR / "sales_analytics.csv", index=False)
    print("Generated sales_analytics.csv")

def generate_education(n=800):
    depts = ["Computer Science", "Mechanical Eng", "Business Admin", "Data Science", "Economics", "Electrical Eng"]
    genders = ["Female", "Male", "Non-binary"]

    rows = []
    for i in range(n):
        dept = random.choice(depts)
        gender = random.choice(genders)
        attendance = round(random.uniform(60.0, 100.0), 1)
        study_hours = round(random.uniform(5.0, 40.0), 1)
        # Final marks strongly correlated with attendance and study hours + noise
        base_marks = 25 + (attendance * 0.4) + (study_hours * 0.8) + random.gauss(0, 5)
        marks = round(min(100.0, max(20.0, base_marks)), 1)
        midterm = round(min(100.0, max(20.0, marks * random.uniform(0.85, 1.05))), 1)

        if marks >= 85:
            grade = "A"
        elif marks >= 70:
            grade = "B"
        elif marks >= 55:
            grade = "C"
        elif marks >= 40:
            grade = "D"
        else:
            grade = "F"

        rows.append({
            "Student_ID": f"STU-{20000 + i}",
            "Department": dept,
            "Gender": gender,
            "Attendance_Pct": attendance,
            "Weekly_Study_Hours": study_hours,
            "Midterm_Marks": midterm,
            "Final_Marks": marks,
            "Grade": grade
        })
    df = pd.DataFrame(rows)
    df.to_csv(SAMPLES_DIR / "student_performance.csv", index=False)
    print("Generated student_performance.csv")

def generate_healthcare(n=600):
    diagnoses = ["Hypertension", "Diabetes Type 2", "Cardiovascular", "Asthma", "Pneumonia", "Healthy"]
    rows = []
    for i in range(n):
        diag = random.choice(diagnoses)
        age = random.randint(18, 85)
        sys_bp = int(random.gauss(130 if diag == "Hypertension" else 118, 15))
        chol = int(random.gauss(220 if diag in ["Hypertension", "Cardiovascular"] else 185, 30))
        los = random.randint(1, 14) if diag != "Healthy" else 1
        base_cost = {"Hypertension": 3200, "Diabetes Type 2": 4500, "Cardiovascular": 12000, "Asthma": 2100, "Pneumonia": 5800, "Healthy": 450}[diag]
        treatment_cost = round(base_cost * (1 + (los * 0.15)) * random.uniform(0.9, 1.2), 2)

        rows.append({
            "Patient_ID": f"PAT-{50000 + i}",
            "Age": age,
            "Gender": random.choice(["Female", "Male"]),
            "Diagnosis": diag,
            "Systolic_BP": sys_bp,
            "Cholesterol": chol,
            "Length_Of_Stay_Days": los,
            "Treatment_Cost": treatment_cost
        })
    df = pd.DataFrame(rows)
    df.to_csv(SAMPLES_DIR / "healthcare_patients.csv", index=False)
    print("Generated healthcare_patients.csv")

def generate_finance(n=1200):
    categories = ["Travel", "Software & Cloud", "Marketing", "Consulting", "Office Supplies", "Payroll", "Entertainment"]
    acct_types = ["Credit Card", "Corporate Wire", "ACH Transfer", "Expense Card"]
    base_date = datetime.date(2025, 1, 1)

    rows = []
    for i in range(n):
        cat = random.choice(categories)
        dt = base_date + datetime.timedelta(days=random.randint(0, 365))
        acct = random.choice(acct_types)
        amount = round(random.choice([
            random.uniform(15.0, 150.0),
            random.uniform(200.0, 1500.0),
            random.uniform(2000.0, 8500.0)
        ]), 2)
        # Random occasional outlier/fraud
        is_fraud = "Yes" if (amount > 7000 and random.random() < 0.25) else "No"

        rows.append({
            "Transaction_ID": f"TXN-{80000 + i}",
            "Transaction_Date": dt.strftime("%Y-%m-%d"),
            "Category": cat,
            "Account_Type": acct,
            "Amount": amount,
            "Approval_Status": random.choice(["Approved", "Approved", "Approved", "Flagged"]),
            "Is_Anomaly": is_fraud
        })
    df = pd.DataFrame(rows)
    df.to_csv(SAMPLES_DIR / "financial_transactions.csv", index=False)
    print("Generated financial_transactions.csv")

if __name__ == "__main__":
    generate_sales()
    generate_education()
    generate_healthcare()
    generate_finance()

def generate_cfpb_complaints(n=2500):
    products = [
        ("Checking or savings account", 0.39),
        ("Credit card or prepaid card", 0.26),
        ("Credit reporting, repair services", 0.12),
        ("Mortgage", 0.10),
        ("Money transfer, virtual currency", 0.06),
        ("Debt collection", 0.04),
        ("Vehicle loan or lease", 0.02),
        ("Payday loan, title loan", 0.01)
    ]
    prod_names = [p[0] for p in products]
    prod_weights = [p[1] for p in products]

    responses = [
        ("Closed with explanation", 0.6565),
        ("Closed with monetary relief", 0.235),
        ("Closed with non-monetary relief", 0.084),
        ("In progress", 0.024),
        ("Closed", 0.0005)
    ]
    resp_names = [r[0] for r in responses]
    resp_weights = [r[1] for r in responses]

    channels = [
        ("Web", 0.726),
        ("Referral", 0.172),
        ("Phone", 0.075),
        ("Postal Mail", 0.021),
        ("Fax", 0.004),
        ("Email", 0.002)
    ]
    chan_names = [c[0] for c in channels]
    chan_weights = [c[1] for c in channels]

    divisions = [
        ("South Atlantic", 0.261),
        ("Pacific", 0.257),
        ("Middle Atlantic", 0.140),
        ("West South Central", 0.088),
        ("East North Central", 0.080),
        ("Mountain", 0.063),
        ("New England", 0.062),
        ("West North Central", 0.027),
        ("East South Central", 0.022)
    ]
    div_names = [d[0] for d in divisions]
    div_weights = [d[1] for d in divisions]

    issues = [
        "Managing an account",
        "Problem with a purchase",
        "Closing an account",
        "Incorrect information",
        "Opening an account",
        "Fees or interest",
        "Trouble during payment process"
    ]
    issue_weights = [0.242, 0.18, 0.16, 0.15, 0.11, 0.10, 0.058]

    states = ["CA", "FL", "TX", "NY", "GA", "NC", "PA", "IL", "OH", "VA"]

    base_date = datetime.date(2017, 1, 1)
    end_date = datetime.date(2023, 12, 31)
    days_span = (end_date - base_date).days

    rows = []
    for i in range(n):
        dt = base_date + datetime.timedelta(days=random.randint(0, days_span))
        prod = random.choices(prod_names, weights=prod_weights)[0]
        resp = random.choices(resp_names, weights=resp_weights)[0]
        chan = random.choices(chan_names, weights=chan_weights)[0]
        div = random.choices(div_names, weights=div_weights)[0]
        iss = random.choices(issues, weights=issue_weights)[0]
        st = "CA" if div == "Pacific" and random.random() < 0.75 else random.choice(states)
        relief = round(random.uniform(25, 1850), 2) if "monetary relief" in resp else 0.0

        rows.append({
            "Complaint_ID": f"CFPB-{100000 + i}",
            "Date_Received": dt.strftime("%Y-%m-%d"),
            "Product": prod,
            "Issue": iss,
            "Company_Response": resp,
            "Submission_Channel": chan,
            "Division": div,
            "State": st,
            "Monetary_Relief_Amount": relief,
            "Timely_Response": "Yes" if random.random() < 0.98 else "No"
        })

    df = pd.DataFrame(rows)
    df.to_csv(SAMPLES_DIR / "cfpb_consumer_complaints.csv", index=False)
    print("Generated cfpb_consumer_complaints.csv")

if __name__ == "__main__":
    generate_cfpb_complaints()
