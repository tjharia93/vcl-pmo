import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class PMONote(Document):
    def before_insert(self):
        if not self.captured_by:
            self.captured_by = frappe.session.user
        if not self.captured_at:
            self.captured_at = now_datetime()

    def before_save(self):
        if self.project and self.status == "Inbox":
            self.status = "Sorted"
        if self.status in {"Sorted", "Converted", "Archived"} and not self.sorted_at:
            self.sorted_at = now_datetime()
