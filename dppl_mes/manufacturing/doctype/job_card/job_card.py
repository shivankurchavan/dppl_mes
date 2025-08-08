# Copyright (c) 2025, IndusWorks and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds


class JobCard(Document):
	def before_save(self):
		if self.actual_start_date_time:
			self.actual_duration = 0

			if self.actual_end_date_time:

				self.actual_duration = time_diff_in_seconds(self.actual_end_date_time, self.actual_start_date_time)
				duration_in_minutes = self.actual_duration / 60
				if duration_in_minutes > 0:
					self.actual_run_rate = self.completed_quantity / duration_in_minutes

			else:
				print("Job Card: No actual end time, calculating duration from start time to now")
				self.actual_duration = time_diff_in_seconds(now(), self.actual_start_date_time)
				duration_in_minutes = self.actual_duration / 60
				if duration_in_minutes > 0:
					self.actual_run_rate = self.completed_quantity / duration_in_minutes


# class JobCard(Document):
#     def before_save(self):
#         if self.start_date_time:
#             end_time = self.end_date_time or now()
#             self.duration = time_diff_in_seconds(end_time, self.start_date_time)
#             if self.duration > 0:
#                 duration_in_minutes = self.duration / 60
#                 self.actual_run_rate = self.completed_quantity / duration_in_minutes if duration_in_minutes > 0 else 0
#             else:
#                 self.actual_run_rate = 0