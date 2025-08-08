# Copyright (c) 2025, IndusWorks and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds, add_to_date, get_time, get_datetime, get_time_str
import datetime


class ShiftPlan(Document):
	pass


@frappe.whitelist()
def create_job_cards(docname):
    """
    Row Validation Requirement:
    If in Job Plan Details Table the no_job checkbox is unchecked and if any of the following fields are empty:
       - operator_name
       - job_one_name
       - job_one_quantity
    Then throw an error message indicating that for the row with machine {machine_name}, operator {operator_name}, job one {job_one_name}, job one quantity {job_one_quantity} is required.
    """

    doc = frappe.get_doc("Shift Plan", docname)
    for item in doc.job_plan_details:
        if not item.no_job:
            if not item.operator_name or not item.job_one_name or not item.job_one_quantity:
                frappe.throw(
                    f"For machine {item.machine_name}, Operator Name, Job 1 Name, Job 1 Target Quantity is required. If no job is to be done, please check the No Job checkbox."
                )

    """
    job_one_duration Validation Requirement:
    1. if in Job Plan Details Table the no_job checkbox is unchecked
    2. If job_two_name is not empty
    3. job_one_duration is empty
    Then throw an error message indicating that for the row with machine {machine_name}, Job 1 Duration is required. 
    """
    for item in doc.job_plan_details:
        if not item.no_job and item.job_two_name and not item.job_one_duration:
            frappe.throw(
                f"For machine {item.machine_name}, Job 1 Duration is required."
            )
    
    """
    Shift start & end time requirements:
    From the Factory Doctype, fetch the Shift Timing for the  doc.factory and doc.shift.

    """
        # Shift start & end time requirements:
    # From the Factory Doctype, fetch the Shift Timing for the doc.factory and doc.shift.

    factory_doc = frappe.get_doc("Factory", doc.factory)
    shift_start = None
    shift_end = None

    for timing in factory_doc.shift_timings:
        if timing.shift_name == doc.shift:
            shift_start = timing.start_time
            shift_end = timing.end_time
            break
    
    # Combine date and time to get full datetime objects
    if isinstance(doc.date, str):
        shift_date = datetime.datetime.strptime(doc.date, "%Y-%m-%d").date()
    else:
        shift_date = doc.date

    shift_start_str = get_time_str(shift_start)
    shift_end_str = get_time_str(shift_end)

    today_shift_start_date_time = datetime.datetime.combine(
        shift_date,
        datetime.datetime.strptime(shift_start_str, "%H:%M:%S").time()
    )
    today_shift_end_date_time = datetime.datetime.combine(
        shift_date,
        datetime.datetime.strptime(shift_end_str, "%H:%M:%S").time()
    )

    if today_shift_end_date_time <= today_shift_start_date_time:
        today_shift_end_date_time += datetime.timedelta(days=1)

    print(f"Shift Start: {today_shift_start_date_time}, Shift End: {today_shift_end_date_time}")
    
    
    created_count = 0

    for row in doc.job_plan_details:
        if row.no_job:
            continue

        base_fields = {
            "date": doc.date,
            "shift": doc.shift,
            "shift_plan": docname,
            "operator": row.operator_name,
            "machine": row.machine_name,
        }

        if row.job_one_name and not row.job_two_name:
            job_card_1 = frappe.new_doc("Job Card")
            job_card_1.update(base_fields)
            job_card_1.update({
                "job_name": row.job_one_name,
                "target_quantity": row.job_one_quantity,
                "job_sequence_number": 1,
                "planned_start_date_time": today_shift_start_date_time,
                "planned_end_date_time": today_shift_end_date_time,
                "planned_duration": abs(time_diff_in_seconds(today_shift_start_date_time, today_shift_end_date_time))
            })
            job_card_1.save()
            created_count += 1
        elif row.job_one_name and row.job_two_name:
            job_one_end_time_str = add_to_date(today_shift_start_date_time, seconds=row.job_one_duration)
            job_card_1 = frappe.new_doc("Job Card")
            job_card_1.update(base_fields)
            job_card_1.update({
                "job_name": row.job_one_name,
                "target_quantity": row.job_one_quantity,
                "job_sequence_number": 1,
                "planned_start_date_time": today_shift_start_date_time,
                "planned_end_date_time": job_one_end_time_str,
                "planned_duration": int(abs(time_diff_in_seconds(today_shift_start_date_time, job_one_end_time_str)))
            })
            job_card_1.save()
            created_count += 1

            job_card_2 = frappe.new_doc("Job Card")
            job_card_2.update(base_fields)
            job_card_2.update({
                "job_name": row.job_two_name,
                "target_quantity": row.job_two_quantity,
                "job_sequence_number": 2,
                "planned_start_date_time": job_one_end_time_str,
                "planned_end_date_time": today_shift_end_date_time,
                "planned_duration": int(abs(time_diff_in_seconds(job_one_end_time_str, today_shift_end_date_time)))
            })
            job_card_2.save()
            created_count += 1