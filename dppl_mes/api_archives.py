import frappe
import json
from frappe import _
from datetime import datetime


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
                "job_name": metrics_data.get("job_name"),
                "job_number": metrics_data.get("job_number"),
                "target_quantity": metrics_data.get("target_quantity"),
                "completed_quantity": metrics_data.get("completed_quantity"),
                "run_rate_indicator": metrics_data.get("run_rate_indicator")
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


# @frappe.whitelist()
# def create_telemetry():
#     if frappe.request.method != "POST":
#         frappe.throw(_("Only POST requests are allowed"), frappe.PermissionError)
#     try:
        
#         # Parse the JSON data from request body
#         if not frappe.request.data:
#             frappe.throw(_("Request body is empty"))
#         data = json.loads(frappe.request.data)
        
#         # Extract fields with validation
#         timestamp = data.get("timestamp")
#         device = data.get("device")
#         machine = data.get("machine")
#         message = data.get("message")
        
#         # Validate required fields
#         if not all([timestamp, device, machine, message]):
#             frappe.throw(_("Missing required fields. Required: timestamp, device, machine, message"))
        
#         # Validate timestamp format
#         try:
#             if isinstance(timestamp, str):
#                 # Try to parse timestamp to ensure it's valid
#                 datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
#         except ValueError:
#             frappe.throw(_("Invalid timestamp format. Use ISO format (YYYY-MM-DD HH:MM:SS)"))
        
#         # Validate that Device and Machine exist (optional but recommended)
#         if not frappe.db.exists("Device", device):
#             frappe.throw(_("Device '{}' does not exist").format(device))
            
#         if not frappe.db.exists("Machine", machine):
#             frappe.throw(_("Machine '{}' does not exist").format(machine))
        
#         # Create new Telemetry document
#         telemetry = frappe.new_doc("Telemetry")
#         telemetry.timestamp = timestamp
#         telemetry.device = device
#         telemetry.machine = machine
#         telemetry.data = message  # This will handle both strings and JSON objects
        
#         # Insert with proper error handling
#         telemetry.insert(ignore_permissions=True)
#         frappe.db.commit()

#         job_metrics = get_job_metrics_internal_function(machine=machine)
#         if job_metrics.get("status") == "success":
#             return {
#                 "status": "success",
#                 "message": "Telemetry record created successfully, sharing job metrics",
#                 "data": {
#                     "machine": machine,
#                     "job_name": job_metrics["data"].get("job_name"),
#                     "job_number": job_metrics["data"].get("job_number"),
#                     "target_quantity": job_metrics["data"].get("target_quantity"),
#                     "completed_quantity": job_metrics["data"].get("completed_quantity"),
#                     "run_rate_indicator": job_metrics["data"].get("run_rate_indicator")
#                 }
#             }
#         else:
#             return {
#                 "status": "success",
#                 "message": "Telemetry record created successfully, but no job metrics found",
#                 "data": {
#                     "machine": machine,
#                     "job_name": job_metrics["data"].get("job_name"),
#                     "job_number": job_metrics["data"].get("job_number"),
#                     "target_quantity": job_metrics["data"].get("target_quantity"),
#                     "completed_quantity": job_metrics["data"].get("completed_quantity"),
#                     "run_rate_indicator": job_metrics["data"].get("run_rate_indicator")
#                 }
#             }


        
#         # return {
#         #     "status": "success",
#         #     "message": "Telemetry record created successfully",
#         #     "telemetry_id": telemetry.name,
#         #     "data": {
#         #         "name": telemetry.name,
#         #         "timestamp": telemetry.timestamp,
#         #         "device": telemetry.device,
#         #         "machine": telemetry.machine
#         #     }
#         # }
        
#     except frappe.ValidationError as e:
#         frappe.log_error(frappe.get_traceback(), "Telemetry Validation Error")
#         frappe.response["http_status_code"] = 400
#         return {
#             "status": "error",
#             "error_type": "validation_error",
#             "message": str(e)
#         }
        
#     except json.JSONDecodeError as e:
#         frappe.log_error(frappe.get_traceback(), "Telemetry JSON Parse Error")
#         frappe.response["http_status_code"] = 400
#         return {
#             "status": "error", 
#             "error_type": "json_error",
#             "message": "Invalid JSON format in request body"
#         }
        
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Create Telemetry Error")
#         frappe.response["http_status_code"] = 500
#         return {
#             "status": "error",
#             "error_type": "server_error", 
#             "message": "Internal server error occurred"
#         }

@frappe.whitelist()
def get_job_metrics_internal_function(machine=None):
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
                "job_number",
                "target_quantity",
                "completed_quantity",
                "target_run_rate",
                "actual_run_rate"
            ],
            order_by="creation desc",
            as_dict=True
        )

        if not job_card:
            return {
                "status": "failure",
                "data": {
                    "job_name": "No Job Running",
                    "job_number": "N/A",
                    "target_quantity": 0,
                    "completed_quantity": 0,
                    "run_rate_indicator": 0
                }
            }

        target_rate = job_card.target_run_rate or 0
        actual_rate = job_card.actual_run_rate or 0
        run_rate_indicator = 1 if actual_rate >= target_rate else 0

        return {
            "status": "success",
            "data": {
                "job_name": job_card.job_name or "",
                "job_number": job_card.job_number or "",
                "target_quantity": job_card.target_quantity or 0,
                "completed_quantity": job_card.completed_quantity or 0,
                "run_rate_indicator": run_rate_indicator
            }
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Error in get_job_metrics for machine {machine}")
        return {
            "status": "error",
            "data": {
                "job_name": "",
                "job_number": "",
                "target_quantity": 0,
                "completed_quantity": 0,
                "run_rate_indicator": 0
            }
        }



@frappe.whitelist()
def get_job_metrics(machine=None):
    """
    Fetch latest 'In Progress' Job Card for a machine and return key metrics.
    Accepts machine as a query parameter (GET request).
    """
    if frappe.request.method != "GET":
        frappe.throw(_("Only GET requests are allowed"), frappe.PermissionError)

    try:
        # Get machine from query params if not provided by Frappe param parsing
        if not machine:
            machine = frappe.form_dict.get("machine")

        # Validate machine
        if not machine or not frappe.db.exists("Machine", machine):
            return {
                "status": "error",
                "message": f"Machine '{machine}' does not exist" if machine else "Machine parameter missing",
                "data": {
                    "job_name": "",
                    "job_number": "",
                    "target_quantity": 0,
                    "completed_quantity": 0,
                    "run_rate_indicator": 0
                }
            }

        # Get latest job card
        job_card = frappe.get_value(
            "Job Card",
            filters={"machine": machine, "status": "In Progress"},
            fieldname=[
                "job_name",
                "job_number",
                "target_quantity",
                "completed_quantity",
                "target_run_rate",
                "actual_run_rate"
            ],
            order_by="creation desc",
            as_dict=True
        )

        if not job_card:
            return {
                "status": "success",
                "message": f"No job in progress for machine {machine}, returning defaults",
                "data": {
                    "job_name": "No Job Running",
                    "job_number": "N/A",
                    "target_quantity": 0,
                    "completed_quantity": 0,
                    "run_rate_indicator": 0
                }
            }

        # Compute run_rate_indicator
        target_rate = job_card.target_run_rate or 0
        actual_rate = job_card.actual_run_rate or 0
        run_rate_indicator = 1 if actual_rate >= target_rate else 0

        return {
            "status": "success",
            "message": "Job metrics retrieved successfully",
            "data": {
                "job_name": job_card.job_name or "",
                "job_number": job_card.job_number or "",
                "target_quantity": job_card.target_quantity or 0,
                "completed_quantity": job_card.completed_quantity or 0,
                "run_rate_indicator": run_rate_indicator
            }
        }

    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Error in get_job_metrics for machine {machine}")
        return {
            "status": "error",
            "message": "Internal server error occurred while fetching job metrics",
            "data": {
                "job_name": "",
                "job_number": "",
                "target_quantity": 0,
                "completed_quantity": 0,
                "run_rate_indicator": 0
            }
        }

        
    

# Optional: Bulk create endpoint for multiple telemetry records
@frappe.whitelist(allow_guest=True)
def create_telemetry_bulk():
    """
    POST API endpoint to create multiple Telemetry documents in bulk
    Expected payload: {
        "records": [
            {
                "timestamp": "2025-06-27 10:30:00",
                "device": "device_name", 
                "machine": "machine_name",
                "message": "data"
            },
            // ... more records
        ]
    }
    """
    if frappe.request.method != "POST":
        frappe.throw(_("Only POST requests are allowed"), frappe.PermissionError)
    
    try:
        data = json.loads(frappe.request.data)
        records = data.get("records", [])
        
        if not records:
            frappe.throw(_("No records provided"))
        
        if len(records) > 1000:  # Limit bulk operations
            frappe.throw(_("Cannot process more than 1000 records at once"))
        
        created_records = []
        errors = []
        
        for i, record in enumerate(records):
            try:
                timestamp = record.get("timestamp")
                device = record.get("device")
                machine = record.get("machine")
                message = record.get("message")
                
                if not all([timestamp, device, machine, message]):
                    errors.append(f"Record {i+1}: Missing required fields")
                    continue
                
                telemetry = frappe.new_doc("Telemetry")
                telemetry.timestamp = timestamp
                telemetry.device = device
                telemetry.machine = machine
                telemetry.data = message
                
                telemetry.insert(ignore_permissions=True)
                created_records.append(telemetry.name)
                
            except Exception as e:
                errors.append(f"Record {i+1}: {str(e)}")
        
        frappe.db.commit()
        
        return {
            "status": "success" if not errors else "partial_success",
            "message": f"Created {len(created_records)} records",
            "created_count": len(created_records),
            "error_count": len(errors),
            "created_records": created_records,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Bulk Create Telemetry Error")
        frappe.response["http_status_code"] = 500
        return {
            "status": "error",
            "message": str(e)
        }