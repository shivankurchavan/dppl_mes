# Copyright (c) 2025, IndusWorks and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, nowdate, nowtime
from datetime import datetime, timedelta, time
import json

class Telemetry(Document):
	def before_save(self):
		timestamp = self.timestamp
		machine = self.machine
		data_str = self.data
		
		try:
			data = json.loads(data_str)
		except json.JSONDecodeError as e:
			frappe.log_error(frappe.get_traceback(), "JSON Decoding Error")

		if "output" in data:
			try:
				output_raw = data["output"]
				if output_raw is None or output_raw == '' or str(output_raw).strip() == '':
					print('Empty or invalid output value detected, skipping output processing')
					return
				output_value = int(output_raw)
				run_rate_value = float(data["run_rate"])
				self.create_output_log(output_value,run_rate_value, timestamp, machine)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Output Parsing Error")
		
		if "status" in data:
			print('Machine Status Exisits')
			try:
				machine_status = data["status"]
				self.downtime_checker(machine_status)
			except Exception as e:
				frappe.log_error(frappe.get_traceback(), "Status Parsing Error")

	def create_output_log(self, output_value,run_rate_value, timestamp, machine):
		try:
			job_card = self.get_job_details(machine, output_value)
			if job_card:
				output_log = frappe.new_doc("Output Log")
				output_log.machine = machine
				output_log.job_card = job_card
				output_log.output = output_value
				output_log.run_rate = run_rate_value
				output_log.timestamp = timestamp
				output_log.save()
				print('Output Log Created')
				print('Updating Job Card Now')
				job_card_doc = frappe.get_doc("Job Card", job_card)
				machine_output_type = frappe.db.get_value("Machine", machine, "output_type")
				if machine_output_type == 'Absolute Values':
					job_card_doc.completed_quantity = output_value
					job_card_doc.save()
				if machine_output_type == 'Relative Values':
					job_card_doc.completed_quantity = job_card_doc.completed_quantity + output_value
					job_card_doc.save()
				print('Job Card Updated')
			else:
				print('No Job Card Found')
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Create Output Log Error")

	def get_job_details(self, machine, output_value):
		"""
		1. run get_active_job Function
		2. if active_job exisits then return active_job else
		3. run start_job function and return active_job

		"""
		try:
			active_job = self.get_active_job(machine)
			print(f'Active Job: {active_job}')
			if active_job:
				print('Active Job Found')
				machine_output_type = frappe.db.get_value("Machine", machine, "output_type")
				if machine_output_type == 'Absolute Values':
					print('Entered Absolute Value Checker Block')
					active_job_doc = frappe.get_doc("Job Card", active_job)
					job_completed_qty = active_job_doc.completed_quantity
					print(f'Job Completed Quantity: {job_completed_qty}')

					if job_completed_qty > 0 and output_value < job_completed_qty:
						print('Output Value Reset Detected, Updating Job Status to Completed')
						active_job_doc.status = "Completed"
						active_job_doc.actual_end_date_time = now()
						active_job_doc.save()
						frappe.db.commit()
						if output_value > 0:
							new_job = self.start_job(machine)
							return new_job
					else:
						return active_job
			else:
				print('Active Job Not Found, Trying To Start New Job')
				if output_value > 0:
					print('Output Value Detected, Checking Previous Job Completion')
					previous_job_counter_reset = previous_job_counter_reset_function(machine, active_job, output_value)
					if previous_job_counter_reset == False:
						print('Counter of Previous Job Still Coming. Not Starting New Job')
						return None
					else:
						new_job = self.start_job(machine)
						return new_job
				else:
					return None
				
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Get Job Details Error")

	def get_active_job(self, machine):
		try:
			active_job_list = frappe.get_all('Job Card', filters={"machine": machine, "status": "In Progress"}, fields=["name"])
			print(active_job_list)
			if active_job_list:
				active_job = active_job_list[0].name
				return active_job
			else:
				return None
		except Exception as e:
			frappe.log_error(f"{frappe.get_traceback()}\nError: {str(e)}", "Get Active Job Error")
	
	def start_job(self, machine):
		"""
		0. In a Try Block do the following
		1. Get current_date
		2. Get current_time
		3. From Machine Get Factory
		4. Based on current_time get shift as current_shift from shift_timings table in Factory Doctype
		5. Based on machine, current_date, current_shift get scheduled_jobs from Job Card Doctype in ascedning order of job_sequence_number
		6. First check status of scheduled_job where job_sequence_number == 1. if the status is 'Not Started' then return then change the status as 'In Progress' and return the job'
		7. If the status of scheduled_job where job_sequence_number == 1 is not 'Not Started' then check for scheduled_job where job_sequence_number == 2. if such job exists then change the status as 'In Progress' and return the job' else return None

		"""
		try:
			current_date = nowdate()
			current_time = datetime.strptime(nowtime(), "%H:%M:%S.%f").time()

			machine_doc = frappe.get_doc("Machine", machine)
			factory = machine_doc.factory
			print(factory)

			# Get current shift
			current_shift = None
			factory_doc = frappe.get_doc("Factory", factory)
			for shift in factory_doc.get("shift_timings"):
				shift_start_time = to_time(shift.start_time)
				print(f'Shift Start Time: {shift_start_time}')
				shift_end_time = to_time(shift.end_time)
				print(f'Shift End Time: {shift_end_time}')

				# Handle overnight shifts
				if shift_start_time <= shift_end_time:
					if shift_start_time <= current_time <= shift_end_time:
						current_shift = shift.shift_name
						print(f'Current Shift: {current_shift}')
						break
				else:  # Overnight shift
					if current_time >= shift_start_time or current_time <= shift_end_time:
						current_shift = shift.shift_name
						print(f'Current Shift: {current_shift}')
						break
			if not current_shift:
				frappe.throw("No active shift found for the current time.")

			# Get scheduled jobs
			scheduled_jobs = frappe.get_all(
				"Job Card",
				filters={
					"machine": machine,
					"date": current_date,
					"shift": current_shift,
				},
				order_by="job_sequence_number asc",
				fields=["name", "status", "job_sequence_number"],
			)

			if not scheduled_jobs:
				return None

			# Check job with sequence number 1
			job_seq_1 = next((job for job in scheduled_jobs if job.job_sequence_number == 1), None)

			if job_seq_1 and job_seq_1.status == "Not Started":
				job_card = frappe.get_doc("Job Card", job_seq_1.name)
				job_card.status = "In Progress"
				job_card.actual_start_date_time = now()
				job_card.save()
				return job_card.name
			else:
				# Check for job with sequence number 2
				job_seq_2 = next((job for job in scheduled_jobs if job.job_sequence_number == 2), None)
				if job_seq_2 and job_seq_2.status == "Not Started":
					job_card = frappe.get_doc("Job Card", job_seq_2.name)
					job_card.status = "In Progress"
					job_card.actual_start_date_time = now()
					job_card.save()
					return job_card.name
				else:
					return None

		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Start Job Error")
				

	def downtime_checker(self, machine_status):
		try:
			existing_downtime_log = self.downtime_record_checker()
			if machine_status == 'running':
				if existing_downtime_log:
					print('Existing Downtime Log Found, Closing Downtime Log')
					self.close_downtime_log(existing_downtime_log)
					print('Downtime Log Closed')
				else:
					print('No Existing Downtime Log Found, No Action Needed')
			elif machine_status == 'stopped':
				if not existing_downtime_log:
					print('No Existing Downtime Log Found, Creating New Downtime Log')
					self.create_downtime_log()
					print('Downtime Log Created')
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Downtime Checker Error")
	
	def downtime_record_checker(self):
		"""Check for existing open downtime logs."""
		print("Downtime Record Checker Called")
		downtime_logs = frappe.get_all(
			"Downtime Log",
			filters={"machine": self.machine, "status": "Open"},
			fields=["name"],
		)
		return downtime_logs[0].name if downtime_logs else None

	def create_downtime_log(self):
		"""Create a new downtime log entry."""
		try:
			downtime_log = frappe.new_doc("Downtime Log")
			downtime_log.machine = self.machine
			downtime_log.created_date = nowdate()
			downtime_log.start_date_time = self.timestamp
			downtime_log.status = "Open"
			downtime_log.save()
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Create Downtime Log Error")

	def close_downtime_log(self, downtime_record):
		"""Close an existing downtime log entry."""
		try:
			downtime_log = frappe.get_doc("Downtime Log", downtime_record)
			downtime_log.end_date_time = now()
			downtime_log.status = "Closed"
			downtime_log.save()
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Close Downtime Log Error")
	

def to_time(val):
    if isinstance(val, time):
        return val
    if isinstance(val, timedelta):
        total_seconds = int(val.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return time(hour=hours, minute=minutes, second=seconds)
    return datetime.strptime(str(val), "%H:%M:%S").time()

def previous_job_counter_reset_function(machine, active_job, output_value):
	"""
	requirements:
	1. Get the job card document previous to the active job
	2. Check if the previous job completed quantity is same as job_completed_qty
	3. if yes then return true else return false
	"""
	previous_job = frappe.get_all(
		"Job Card",
		filters={"machine": machine, "status": "Completed"},
		order_by="end_date_time desc",
		fields=["completed_quantity"],
		limit=1
	)
	if previous_job:
		print(f'Previous Job Found: {previous_job}')
		if previous_job[0].completed_quantity == output_value:
			print('Previous Job Completed Quantity Matches Output Value')
			return False