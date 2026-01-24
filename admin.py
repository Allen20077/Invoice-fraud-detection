from flask import Blueprint, redirect, url_for
from database import update_status

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/approve/<invoice_id>")
def approve(invoice_id):
    update_status(invoice_id, "APPROVED")
    return redirect(url_for("index"))

@admin_bp.route("/reject/<invoice_id>")
def reject(invoice_id):
    update_status(invoice_id, "REJECTED")
    return redirect(url_for("index"))
