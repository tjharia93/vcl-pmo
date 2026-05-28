import frappe
from frappe.model.document import Document


class PMOShift(Document):
    def before_save(self):
        if self.requires_uat and not self.uat_case:
            self.uat_case = _ensure_uat_case_for_shift(self)
        if self.requires_oat and not self.oat_check:
            self.oat_check = _ensure_oat_check_for_shift(self)


def _ensure_uat_case_for_shift(shift):
    case_id = f"UAT-{shift.shift_id}"
    existing = frappe.db.get_value("PMO UAT Case", {"uat_case_id": case_id}, "name")
    if existing:
        # Backfill bucket / linked_shift on existing cases that pre-date the bucket schema.
        frappe.db.set_value("PMO UAT Case", existing, {
            "bucket": shift.shift_id,
            "linked_shift": shift.name,
            "linked_plan": shift.linked_plan or None,
            "linked_task": shift.linked_task or None,
        }, update_modified=False)
        return existing
    doc = frappe.get_doc({
        "doctype": "PMO UAT Case",
        "uat_case_id": case_id,
        "project": shift.project,
        "requirement": shift.linked_requirement or None,
        "bucket": shift.shift_id,
        "linked_shift": shift.name,
        "linked_plan": shift.linked_plan or None,
        "linked_task": shift.linked_task or None,
        "description": f"UAT for shift {shift.shift_id}: {shift.title}",
        "acceptance_criteria": shift.description or "",
    })
    doc.insert(ignore_permissions=False)
    return doc.name


def _ensure_oat_check_for_shift(shift):
    check_id = f"OAT-{shift.shift_id}"
    existing = frappe.db.get_value("PMO OAT Check", {"check_id": check_id}, "name")
    if existing:
        frappe.db.set_value("PMO OAT Check", existing, {
            "bucket": shift.shift_id,
            "linked_shift": shift.name,
            "linked_plan": shift.linked_plan or None,
            "linked_task": shift.linked_task or None,
        }, update_modified=False)
        return existing
    doc = frappe.get_doc({
        "doctype": "PMO OAT Check",
        "check_id": check_id,
        "project": shift.project,
        "area": "Shift",
        "bucket": shift.shift_id,
        "linked_shift": shift.name,
        "linked_plan": shift.linked_plan or None,
        "linked_task": shift.linked_task or None,
        "check": f"OAT for shift {shift.shift_id}: {shift.title}",
        "acceptance_criteria": shift.description or "",
    })
    doc.insert(ignore_permissions=False)
    return doc.name
