import pandas as pd
from sklearn.ensemble import IsolationForest

# Load datasets
po_df = pd.read_csv("purchase_orders.csv")
invoice_df = pd.read_csv("invoices.csv")

# Merge invoice with PO
df = invoice_df.merge(po_df, on="PO_ID", how="left")

# Rule-based checks
def rule_check(row):
    if pd.isna(row["PO_Amount"]):
        return "Invalid PO"
    if row["Vendor_x"] != row["Vendor_y"]:
        return "Vendor Mismatch"
    if row["Invoice_Amount"] > row["PO_Amount"] * 1.05:
        return "Overbilling"
    return "Valid"

df["Rule_Status"] = df.apply(rule_check, axis=1)

# ML anomaly detection
ml_data = df[["Invoice_Amount"]].fillna(0)
model = IsolationForest(n_estimators=100, contamination=0.25, random_state=42)
df["Anomaly"] = model.fit_predict(ml_data)
df["ML_Status"] = df["Anomaly"].map({-1: "Suspicious", 1: "Normal"})

# Duplicate invoice detection
duplicates = df.duplicated(subset=["PO_ID", "Vendor_x", "Invoice_Amount"], keep=False)
df.loc[duplicates, "Rule_Status"] = "Duplicate Invoice"

# Final report
final_report = df[
    ["Invoice_ID", "PO_ID", "Vendor_x", "Invoice_Amount", "Rule_Status", "ML_Status"]
].rename(columns={"Vendor_x": "Vendor"})

final_report.to_csv("output_report.csv", index=False)

print("Fraud Detection Completed")
print(final_report)

