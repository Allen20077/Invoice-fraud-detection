import pandas as pd
import os
from sklearn.ensemble import IsolationForest
import re

# GSTIN format: 15 chars (state code + PAN + checksum)
def is_valid_gstin(gstin):
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    return bool(re.match(pattern, gstin))
# Indian GST state codes (partial list – enough for validation)
GST_STATE_CODES = {
    "29": "Karnataka",
    "27": "Maharashtra",
    "07": "Delhi",
    "09": "Uttar Pradesh",
    "33": "Tamil Nadu",
    "24": "Gujarat",
    "19": "West Bengal"
}

def is_valid_state_code(gstin):
    return gstin[:2] in GST_STATE_CODES


# Trusted vendor list (enterprise master data)
TRUSTED_VENDORS = ["ABC Ltd", "XYZ Pvt"]

# Valid invoice ID pattern
def is_valid_invoice_format(invoice_id):
    return invoice_id.startswith("INV") and invoice_id[3:].isdigit()

# Load data once
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

po_path = os.path.join(BASE_DIR, "purchase_orders.csv")
invoice_path = os.path.join(BASE_DIR, "invoices.csv")

po_df = pd.read_csv(po_path)
invoice_df = pd.read_csv(invoice_path)


# Merge data
df = invoice_df.merge(po_df, on="PO_ID", how="left")

# Rule-based check
def rule_check(row):
    if pd.isna(row["PO_Amount"]):
        return "Invalid PO"
    if row["Vendor_x"] != row["Vendor_y"]:
        return "Vendor Mismatch"
    if row["Invoice_Amount"] > row["PO_Amount"] * 1.05:
        return "Overbilling"
    return "Valid"

df["Rule_Status"] = df.apply(rule_check, axis=1)

# Duplicate detection
duplicates = df.duplicated(
    subset=["PO_ID", "Vendor_x", "Invoice_Amount"], keep=False
)
df.loc[duplicates, "Rule_Status"] = "Duplicate Invoice"

# ML anomaly detection
ml_data = df[["Invoice_Amount"]].fillna(0)
model = IsolationForest(n_estimators=100, contamination=0.25, random_state=42)
df["ML_Status"] = model.fit_predict(ml_data)
df["ML_Status"] = df["ML_Status"].map({1: "Normal", -1: "Suspicious"})

def check_invoice(invoice_id):
    record = df[df["Invoice_ID"] == invoice_id]

    # Invoice not found
    if record.empty:
        return {
            "Invoice_ID": invoice_id,
            "PO_ID": "—",
            "Vendor": "—",
            "Invoice_Amount": "—",
            "Rule_Status": "Invoice Not Found",
            "ML_Status": "Unverified",
            "Risk_Score": 90,
            "Reasons": "Invoice ID not found in enterprise records"
        }

    row = record.iloc[0]
    risk_score = 0
    reasons = []
    
    # GST Validation (if GSTIN exists in Vendor column)
    vendor = row["Vendor_x"]

    # Example assumption: Vendor field may contain GSTIN like "ABC Ltd | 29ABCDE1234F1Z5"
    if "|" in vendor:
        vendor_name, gstin = vendor.split("|")
        gstin = gstin.strip()

        if not is_valid_gstin(gstin):
            risk_score += 20
            reasons.append("Invalid GSTIN format")

        elif not is_valid_state_code(gstin):
            risk_score += 10
            reasons.append("Invalid GST state code")

    # GST amount sanity check (assume 18% standard GST)
    invoice_amount = row["Invoice_Amount"]

    # GST breakup
    gst_rate = 0.18
    gst_amount = invoice_amount * gst_rate

    cgst = sgst = igst = 0

    # Intra-state vs Inter-state (example logic)
    if "|" in row["Vendor_x"]:
        _, gstin = row["Vendor_x"].split("|")
        gstin = gstin.strip()

        if gstin[:2] == "29":  # Karnataka example
            cgst = gst_amount / 2
            sgst = gst_amount / 2
        else:
            igst = gst_amount

    expected_tax = invoice_amount * 0.18
    if expected_tax < 0:
        risk_score += 10
        reasons.append("Invalid tax calculation")
    elif expected_tax > invoice_amount * 0.25:
        risk_score += 10
        reasons.append("Excessive tax amount")

    # Invoice format check
    if not is_valid_invoice_format(invoice_id):
        risk_score += 20
        reasons.append("Invalid invoice format")

    # Vendor verification
    if row["Vendor_x"] not in TRUSTED_VENDORS:
        risk_score += 30
        reasons.append("Unregistered vendor")

    # Rule-based fraud
    if row["Rule_Status"] != "Valid":
        risk_score += 30
        reasons.append(row["Rule_Status"])

    # ML anomaly
    if row["ML_Status"] == "Suspicious":
        risk_score += 20
        reasons.append("Anomalous amount")

    risk_score = min(risk_score, 100)

    return {
        "Invoice_ID": row["Invoice_ID"],
        "PO_ID": row["PO_ID"],
        "Vendor": row["Vendor_x"],
        "Invoice_Amount": row["Invoice_Amount"],
        "Rule_Status": row["Rule_Status"],
        "ML_Status": row["ML_Status"],
        "Risk_Score": risk_score,
        "Reasons": ", ".join(reasons) if reasons else "No issues detected",
        "CGST": round(cgst, 2),
        "SGST": round(sgst, 2),
        "IGST": round(igst, 2)
    }

def generate_invoice_id():
    global df

    if df.empty:
        return "INV1001"

    last_id = df["Invoice_ID"].str.replace("INV", "").astype(int).max()
    return f"INV{last_id + 1}"
def add_invoice_without_id(po_id, vendor, amount, date):
    global df

    invoice_id = generate_invoice_id()

    new_row = {
        "Invoice_ID": invoice_id,
        "PO_ID": po_id,
        "Vendor_x": vendor,
        "Invoice_Amount": amount,
        "Date": date
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(invoice_path, index=False)

    return invoice_id
