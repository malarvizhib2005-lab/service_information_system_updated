import csv
import io
import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    make_response, abort
)
from database import get_connection, ensure_database_schema

ensure_database_schema()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-only-change-me")

STATUSES = ["RECEIVED", "ACKNOWLEDGED", "WIP", "TECH-COMPLETED", "CLOSED"]
DEFAULT_LOCATIONS = [
    "Ahmedabad", "Ambarnath", "Andhra Pradesh", "Arunachal Pradesh", "Assam",
    "Aurangabad", "Bangalore", "Bangladesh", "Baruch", "Bhiwadi", "Bhopal",
    "Bihar", "Chandigarh", "Chennai", "Coimbatore", "Delhi", "Goa",
    "Gujarat", "Hyderabad", "Indore", "Jaipur", "Jammu and Kashmir",
    "Jharkhand", "Karnataka", "Kerala", "Kolkata", "Lucknow", "Madhya Pradesh",
    "Maharashtra", "Manipur", "Meghalaya", "Mumbai", "Nagpur", "Odisha",
    "Pune", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu", "Telangana",
    "Thane", "Uttar Pradesh", "Uttarakhand", "West Bengal"
]
DEFAULT_RELIGIONS = [
    "Hindu", "Muslim", "Christian", "Sikh", "Buddhist", "Jain", "Parsi",
    "Jewish", "Bahá'í", "Other", "Prefer not to say"
]
REGIONS = ["International", "North", "South", "SouthCentral", "West"]


def get_filter_options():
    """Return complete dropdown options: default values plus database values."""
    location_rows = query_db(
        "SELECT DISTINCT locationName FROM serviceInfo "
        "WHERE locationName IS NOT NULL AND TRIM(locationName) <> '' "
        "ORDER BY locationName"
    )
    region_rows = query_db(
        "SELECT DISTINCT regionName FROM serviceInfo "
        "WHERE regionName IS NOT NULL AND TRIM(regionName) <> '' "
        "ORDER BY regionName"
    )
    religion_rows = query_db(
        "SELECT DISTINCT religionName FROM serviceInfo "
        "WHERE religionName IS NOT NULL AND TRIM(religionName) <> '' "
        "ORDER BY religionName"
    )
    locations = sorted(set(DEFAULT_LOCATIONS) | {r["locationName"].strip() for r in location_rows if r.get("locationName")})
    regions = sorted(set(REGIONS) | {r["regionName"].strip() for r in region_rows if r.get("regionName")})
    religions = sorted(set(DEFAULT_RELIGIONS) | {r["religionName"].strip() for r in religion_rows if r.get("religionName")})
    return locations, regions, religions


def query_db(sql, params=(), one=False):
    """Run a SELECT query and return dictionaries."""
    conn = get_connection()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        result = cur.fetchone() if one else cur.fetchall()
        cur.close()
        return result
    finally:
        conn.close()


def execute_db(sql, params=()):
    """Run INSERT/UPDATE/DELETE and commit the transaction."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        new_id = cur.lastrowid
        cur.close()
        return new_id
    finally:
        conn.close()


def get_service_or_404(service_id):
    service = query_db("SELECT * FROM serviceInfo WHERE id = %s", (service_id,), one=True)
    if not service:
        abort(404)
    return service


def calculate_tat(service):
    """Calculate elapsed days and compare them with the configured target."""
    start = service.get("requestTime")
    end = service.get("closedAt") if service.get("status") == "CLOSED" and service.get("closedAt") else datetime.now()
    if not start:
        return None, "Unknown"
    days = max(0, (end - start).total_seconds() / 86400)
    target = service.get("tatTargetDays") or 7
    return round(days, 2), ("Within TAT" if days <= target else "TAT Breached")


def normalize_filter_value(value):
    """Treat 'all' or blank as no filter selected."""
    if value is None:
        return ""
    value = str(value).strip()
    return "" if value.lower() == "all" else value


@app.template_filter("datefmt")
def datefmt(value):
    return value.strftime("%d-%m-%Y %I:%M %p") if value else "-"


@app.route("/")
def index():
    clauses, params = [], []
    search = request.args.get("search", "").strip()
    date_range = normalize_filter_value(request.args.get("date_range", ""))
    location = normalize_filter_value(request.args.get("location", ""))
    region = normalize_filter_value(request.args.get("region", ""))
    religion = normalize_filter_value(request.args.get("religion", ""))
    status = normalize_filter_value(request.args.get("status", ""))
    reopened = normalize_filter_value(request.args.get("reopened", ""))
    tat_filter = normalize_filter_value(request.args.get("tat_filter", ""))

    if search:
        like = f"%{search}%"
        clauses.append("(CAST(id AS CHAR) LIKE %s OR name LIKE %s OR email LIKE %s OR phoneNumber LIKE %s OR productType LIKE %s)")
        params.extend([like] * 5)

    if location:
        clauses.append("locationName = %s")
        params.append(location)
    if region:
        clauses.append("regionName = %s")
        params.append(region)
    if religion:
        clauses.append("religionName = %s")
        params.append(religion)
    if status:
        clauses.append("status = %s")
        params.append(status)
    if reopened == "1":
        clauses.append("isReopened = 1")

    # Date range is based on requestTime.
    date_sql = {
        "7": "requestTime >= DATE_SUB(NOW(), INTERVAL 7 DAY)",
        "30": "requestTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)",
        "90": "requestTime >= DATE_SUB(NOW(), INTERVAL 90 DAY)",
        "month": "YEAR(requestTime)=YEAR(CURDATE()) AND MONTH(requestTime)=MONTH(CURDATE())",
        "last_month": "requestTime >= DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%Y-%m-01') AND requestTime < DATE_FORMAT(CURDATE(), '%Y-%m-01')",
        "financial_year": "(requestTime >= STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE()), YEAR(CURDATE())-1), '-04-01'), '%Y-%m-%d') AND requestTime < STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE())+1, YEAR(CURDATE())), '-04-01'), '%Y-%m-%d'))",
        "fy_current": "(requestTime >= STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE()), YEAR(CURDATE())-1), '-04-01'), '%Y-%m-%d') AND requestTime < STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE())+1, YEAR(CURDATE())), '-04-01'), '%Y-%m-%d'))",
    }
    if date_range in date_sql:
        clauses.append(date_sql[date_range])

    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    services = query_db("SELECT * FROM serviceInfo" + where + " ORDER BY requestTime DESC, id DESC", params)
    locations, regions, religions = get_filter_options()

    for row in services:
        row["tat_days"], row["tat_status"] = calculate_tat(row)

    if tat_filter == "within":
        services = [s for s in services if s["tat_status"] == "Within TAT"]
    elif tat_filter == "breached":
        services = [s for s in services if s["tat_status"] == "TAT Breached"]

    return render_template(
        "index.html", services=services, locations=locations, regions=regions,
        religions=religions, statuses=STATUSES, filters=request.args
    )


@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        form = request.form
        name = form.get("name", "").strip()
        if not name:
            flash("Customer name is required.", "error")
            locations, regions, religions = get_filter_options()
            return render_template("form.html", mode="Add", service=form, statuses=STATUSES, locations=locations, regions=regions, religions=religions)

        status = form.get("status", "RECEIVED")
        if status not in STATUSES:
            status = "RECEIVED"

        execute_db("""
            INSERT INTO serviceInfo
            (name, email, customerID, companyName, customerManual, phoneNumber,
             productID, productType, issueDescription, locationName, religionName,
             regionName, subcategoryName, status, userID, remarks, tatTargetDays, reqIpAddr)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            name, form.get("email") or None, form.get("customerID") or None,
            form.get("companyName") or None, 1 if form.get("customerManual") else 0,
            form.get("phoneNumber") or None, form.get("productID") or None,
            form.get("productType") or None, form.get("issueDescription") or None,
            form.get("locationName") or None, form.get("religionName") or None,
            form.get("regionName") or None, form.get("subcategoryName") or None,
            status, form.get("userID") or None, form.get("remarks") or None,
            form.get("tatTargetDays") or 7, request.remote_addr
        ))
        flash("Service record created successfully.", "success")
        return redirect(url_for("index"))

    locations, regions, religions = get_filter_options()
    return render_template("form.html", mode="Add", service={}, statuses=STATUSES, locations=locations, regions=regions, religions=religions)


@app.route("/view/<int:service_id>")
def view(service_id):
    service = get_service_or_404(service_id)
    service["tat_days"], service["tat_status"] = calculate_tat(service)
    return render_template("view.html", service=service)


@app.route("/edit/<int:service_id>", methods=["GET", "POST"])
def edit(service_id):
    service = get_service_or_404(service_id)
    if request.method == "POST":
        form = request.form
        status = form.get("status", "RECEIVED")
        if status not in STATUSES:
            status = service["status"]
        closed_at = datetime.now() if status == "CLOSED" and service["status"] != "CLOSED" else service.get("closedAt")
        if status != "CLOSED":
            closed_at = None

        execute_db("""
            UPDATE serviceInfo SET
            name=%s, email=%s, customerID=%s, companyName=%s, customerManual=%s,
            phoneNumber=%s, productID=%s, productType=%s, issueDescription=%s,
            locationName=%s, religionName=%s, regionName=%s, subcategoryName=%s, status=%s,
            userID=%s, remarks=%s, tatTargetDays=%s, closedAt=%s
            WHERE id=%s
        """, (
            form.get("name", "").strip(), form.get("email") or None,
            form.get("customerID") or None, form.get("companyName") or None,
            1 if form.get("customerManual") else 0, form.get("phoneNumber") or None,
            form.get("productID") or None, form.get("productType") or None,
            form.get("issueDescription") or None, form.get("locationName") or None,
            form.get("religionName") or None, form.get("regionName") or None,
            form.get("subcategoryName") or None, status, form.get("userID") or None,
            form.get("remarks") or None, form.get("tatTargetDays") or 7, closed_at, service_id
        ))
        flash("Service record updated successfully.", "success")
        return redirect(url_for("index"))

    locations, regions, religions = get_filter_options()
    return render_template("form.html", mode="Edit", service=service, statuses=STATUSES, locations=locations, regions=regions, religions=religions)


@app.route("/delete/<int:service_id>", methods=["POST"])
def delete(service_id):
    get_service_or_404(service_id)
    execute_db("DELETE FROM serviceInfo WHERE id = %s", (service_id,))
    flash("Service record deleted.", "success")
    return redirect(url_for("index"))


@app.route("/reopen/<int:service_id>", methods=["POST"])
def reopen(service_id):
    get_service_or_404(service_id)
    execute_db(
        "UPDATE serviceInfo SET status='WIP', isReopened=1, closedAt=NULL WHERE id=%s",
        (service_id,)
    )
    flash("Service case reopened.", "success")
    return redirect(url_for("index"))


@app.route("/export")
def export_csv():
    # Export respects the active filters by reusing the current list query.
    # Redirecting users to the filtered CSV endpoint keeps the UI simple.
    args = request.args.to_dict(flat=True)
    clauses, params = [], []
    search = normalize_filter_value(args.get("search", "")).strip()
    date_range = normalize_filter_value(args.get("date_range", ""))
    if search:
        like = f"%{search}%"
        clauses.append("(CAST(id AS CHAR) LIKE %s OR name LIKE %s OR email LIKE %s OR phoneNumber LIKE %s OR productType LIKE %s)")
        params.extend([like] * 5)
    for key, column in [("location", "locationName"), ("region", "regionName"), ("religion", "religionName"), ("status", "status")]:
        value = normalize_filter_value(args.get(key, ""))
        if value:
            clauses.append(f"{column} = %s")
            params.append(value)
    if date_range in {"financial_year", "fy_current"}:
        clauses.append("(requestTime >= STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE()), YEAR(CURDATE())-1), '-04-01'), '%Y-%m-%d') AND requestTime < STR_TO_DATE(CONCAT(IF(MONTH(CURDATE()) >= 4, YEAR(CURDATE())+1, YEAR(CURDATE())), '-04-01'), '%Y-%m-%d'))")
    elif date_range == "7":
        clauses.append("requestTime >= DATE_SUB(NOW(), INTERVAL 7 DAY)")
    elif date_range == "30":
        clauses.append("requestTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)")
    elif date_range == "90":
        clauses.append("requestTime >= DATE_SUB(NOW(), INTERVAL 90 DAY)")
    elif date_range == "month":
        clauses.append("YEAR(requestTime)=YEAR(CURDATE()) AND MONTH(requestTime)=MONTH(CURDATE())")
    elif date_range == "last_month":
        clauses.append("requestTime >= DATE_FORMAT(CURDATE() - INTERVAL 1 MONTH, '%Y-%m-01') AND requestTime < DATE_FORMAT(CURDATE(), '%Y-%m-01')")
    if normalize_filter_value(args.get("reopened", "")) == "1":
        clauses.append("isReopened = 1")
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    rows = query_db("SELECT * FROM serviceInfo" + where + " ORDER BY requestTime DESC", params)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Case ID", "Requested", "Name", "Email", "Phone", "Product", "Region", "Religion", "Status", "Location", "Remarks"])
    for row in rows:
        writer.writerow([row["id"], row["requestTime"], row["name"], row["email"],
                         row["phoneNumber"], row["productType"], row["regionName"],
                         row.get("religionName"), row["status"], row["locationName"], row["remarks"]])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=service_records.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
