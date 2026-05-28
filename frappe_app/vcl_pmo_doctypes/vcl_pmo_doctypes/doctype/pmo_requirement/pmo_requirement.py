import frappe
from frappe.model.document import Document


class PMORequirement(Document):
    def before_validate(self):
        if not self.requirement_id and self.project:
            self.requirement_id = self.next_requirement_id()

    def next_requirement_id(self):
        project_short = frappe.db.get_value("PMO Project", self.project, "project_short") or "REQ"
        prefix = f"REQ-{str(project_short).upper()}"
        count = frappe.db.count("PMO Requirement") + 1
        while True:
            requirement_id = f"{prefix}-{count:04d}"
            if not frappe.db.exists("PMO Requirement", {"requirement_id": requirement_id}):
                return requirement_id
            count += 1
