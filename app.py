from flask import Flask, request, render_template_string
from fraud_logic import check_invoice
import pytesseract
from PIL import Image
import os
from database import init_db, add_invoice, get_invoice
from admin import admin_bp


app = Flask(__name__)
app.register_blueprint(admin_bp)
init_db()
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)


# Uncomment if Tesseract is not in PATH
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

import re

import re

def extract_invoice_id(image_path):
    try:
        import pytesseract
        from PIL import Image
        import re

        text = pytesseract.image_to_string(Image.open(image_path))
        match = re.search(r"\bINV\d+\b", text)
        return match.group().strip().upper() if match else None
    except Exception:
        # OCR not available on Render
        return None


HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invoice Fraud Detection</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">

    <style>
        body {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            font-family: 'Inter', sans-serif;
            color: white;
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        .card {
            width: 430px;
            background: #111827;
            border-radius: 16px;
            padding: 28px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        }

        .title {
            text-align: center;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
        }

        .search-box {
            display: flex;
            align-items: center;
            background: #1f2933;
            border-radius: 12px;
            padding: 10px;
        }

        .search-box input[type="text"] {
            flex: 1;
            background: transparent;
            border: none;
            outline: none;
            color: white;
            font-size: 14px;
            padding: 8px;
        }

        .upload-label {
            cursor: pointer;
            margin-right: 10px;
            font-size: 18px;
        }

        .search-box button {
            background: #2563eb;
            border: none;
            color: white;
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }

        input[type="file"] {
            display: none;
        }

        .result {
            background: #1f2933;
            border-radius: 12px;
            padding: 16px;
            margin-top: 20px;
            font-size: 14px;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 12px;
        }

        .safe { background: #16a34a; }
        .danger { background: #dc2626; }
        .warn { background: #ca8a04; }

        footer {
            text-align: center;
            margin-top: 14px;
            font-size: 12px;
            color: #9ca3af;
        }
    </style>
</head>

<body>

<div class="card">
    <div class="title">Invoice Matching & Fraud Detection</div>

    <form method="POST" enctype="multipart/form-data">
        <div class="search-box">
            <label class="upload-label">
                📎
                <input type="file" name="invoice_image" accept=".png,.jpg,.jpeg">
            </label>

            <input type="text" name="invoice_id" placeholder="Search Invoice ID (e.g. INV201)">
            <button type="submit">Check</button>
        </div>
    </form>

    {% if invoice_id %}
        <p style="margin-top:10px;"><b>Detected Invoice:</b> {{ invoice_id }}</p>
    {% endif %}

    {% if result %}
    <div class="result">
        <p><b>PO ID:</b> {{ result.PO_ID }}</p>
        <p><b>Vendor:</b> {{ result.Vendor }}</p>
        <p><b>Amount:</b> ₹{{ result.Invoice_Amount }}</p>
        <p><b>CGST:</b> ₹{{ result.CGST }}</p>
<p><b>SGST:</b> ₹{{ result.SGST }}</p>
<p><b>IGST:</b> ₹{{ result.IGST }}</p>

<p><b>Status:</b> {{ result.Status }}</p>
<a href="/approve/{{ result.Invoice_ID }}">Approve</a> |
<a href="/reject/{{ result.Invoice_ID }}">Reject</a>

        <p>
            <b>Rule Status:</b>
            <span class="badge {{ 'safe' if result.Rule_Status == 'Valid' else 'danger' }}">
                {{ result.Rule_Status }}
            </span>
        </p>

        <p>
            <b>ML Status:</b>
            <span class="badge {{ 'safe' if result.ML_Status == 'Normal' else 'warn' }}">
                {{ result.ML_Status }}
            </span>
        </p>
        <p><b>Fraud Risk Score:</b> {{ result.Risk_Score }}/100</p>
<p><b>Reason:</b> {{ result.Reasons }}</p>
<p><b>GST Validation:</b>
{% if 'GST' in result.Reasons %}
    ❌ Failed
{% else %}
    ✅ Passed
{% endif %}
</p>


    </div>
    {% elif invoice_id %}
        <div class="result">Invoice not found.</div>
    {% endif %}

    <footer>Invoice Fraud Detection System</footer>
</div>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    invoice_id = None

    if request.method == "POST":
        

        # Manual search (PRIORITY)
        invoice_id = request.form.get("invoice_id")
        invoice_id = invoice_id.strip() if invoice_id else None

        # Image upload ONLY if search is empty
        if not invoice_id:
            file = request.files.get("invoice_image")
            if file and file.filename:
                path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
                file.save(path)
                invoice_id = extract_invoice_id(path)

        if invoice_id:
            result = check_invoice(invoice_id)

    return render_template_string(
        HTML_PAGE,
        result=result,
        invoice_id=invoice_id
    )
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
