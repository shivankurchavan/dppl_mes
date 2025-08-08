import frappe
import json
from frappe import _
from datetime import datetime
from frappe.utils import now, nowdate, nowtime


@frappe.whitelist()
def create_telemetry():
    if frappe.request.method != "POST":
        frappe.throw(_("Only POST requests are allowed"), frappe.PermissionError)
    try:
        # Parse the JSON data from request body
        if not frappe.request.data:
            frappe.throw(_("Request body is empty"))
        data = json.loads(frappe.request.data)
        
        # Extract fields with validation
        timestamp = data.get("timestamp")
        device = data.get("device")
        machine = data.get("machine")
        message = data.get("message")
        
        # Validate required fields
        if not all([timestamp, device, machine, message]):
            frappe.throw(_("Missing required fields. Required: timestamp, device, machine, message"))
        
        # Validate timestamp format
        try:
            if isinstance(timestamp, str):
                datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            frappe.throw(_("Invalid timestamp format. Use ISO format (YYYY-MM-DD HH:MM:SS)"))
        
        # Validate that Device and Machine exist
        if not frappe.db.exists("Device", device):
            frappe.throw(_("Device '{}' does not exist").format(device))
        if not frappe.db.exists("Machine", machine):
            frappe.throw(_("Machine '{}' does not exist").format(machine))
        
        # Create new Telemetry document
        telemetry = frappe.new_doc("Telemetry")
        telemetry.timestamp = timestamp
        telemetry.device = device
        telemetry.machine = machine
        telemetry.data = message
        telemetry.insert(ignore_permissions=True)
        frappe.db.commit()

        job_metrics = get_job_metrics_internal_function(machine=machine)
        metrics_data = job_metrics.get("data", {})

        return {
            "status": "success",
            "message": "Telemetry record created successfully. Sharing job metrics.",
            "data": {
                "machine": machine,
                "job_metrics": metrics_data
            }
        }
        
    except frappe.ValidationError as e:
        frappe.log_error(frappe.get_traceback(), "Telemetry Validation Error")
        frappe.response["http_status_code"] = 400
        return {
            "status": "error",
            "error_type": "validation_error",
            "message": str(e)
        }
        
    except json.JSONDecodeError as e:
        frappe.log_error(frappe.get_traceback(), "Telemetry JSON Parse Error")
        frappe.response["http_status_code"] = 400
        return {
            "status": "error", 
            "error_type": "json_error",
            "message": "Invalid JSON format in request body"
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Telemetry Error")
        frappe.response["http_status_code"] = 500
        return {
            "status": "error",
            "error_type": "server_error", 
            "message": "Internal server error occurred"
        }




@frappe.whitelist()
def get_job_metrics_internal_function(machine=None):
    print(f"Fetching job metrics for machine: {machine}")
    """
    Fetch latest 'In Progress' Job Card for a machine and return key metrics.
    Always returns metrics inside a 'data' key.
    """
    try:
        job_card = frappe.get_value(
            "Job Card",
            filters={"machine": machine, "status": "In Progress"},
            fieldname=[
                "job_name",
                "target_quantity",
                "completed_quantity",
                "planned_start_date_time",
                "planned_duration"
            ],
            order_by="creation desc",
            as_dict=True
        )

        if not job_card:
            return {
                "status": "failure",
                "data": {
                    "job_name": "No Job Running",
                    "target_quantity": 0,
                    "completed_quantity": 0,
                    "balance_quantity": 0,
                    "run_rate_indicator": 0,
                    "current_time": now()
                }
            }

        # Calculate Time Spent as difference between now and planned start time
        planned_start_time = job_card.planned_start_date_time
        current_time = datetime.now()
        time_spent = current_time - planned_start_time
        time_spent_in_seconds = time_spent.total_seconds()
        total_time = job_card.planned_duration
        ideal_quantity = (time_spent.total_seconds() / total_time) * job_card.target_quantity if total_time else 0
        actual_quantity = job_card.completed_quantity or 0
        balance_quantity = job_card.target_quantity - actual_quantity

        print(f'Time Spent: {time_spent_in_seconds}, Total Time: {total_time}, Ideal Quantity: {ideal_quantity}, Actual Quantity: {actual_quantity}, Balance Quantity: {balance_quantity}')

        if actual_quantity >= ideal_quantity:
            run_rate_indicator = 1
        else:
            run_rate_indicator = 0

        return {
            "status": "success",
            "data": {
                "job_name": job_card.job_name or "",
                "target_quantity": job_card.target_quantity or 0,
                "completed_quantity": job_card.completed_quantity or 0,
                "balance_quantity": balance_quantity or 0,
                "run_rate_indicator": run_rate_indicator,
                "current_time": now()
            }
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Error in get_job_metrics for machine {machine}")
        return {
            "status": "error",
            "data": {
                "job_name": "",
                "target_quantity": 0,
                "completed_quantity": 0,
                "run_rate_indicator": 0
            }
        }


