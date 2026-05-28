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
        return existing
    doc = frappe.get_doc({
        "doctype": "PMO UAT Case",
        "uat_case_id": case_id,
        "project": shift.project,
        "requirement": shift.linked_requirement or None,
        "description": f"UAT for shift {shift.shift_id}: {shift.title}",
        "acceptance_criteria": shift.description or "",
    })
    doc.insert(ignore_permissions=False)
    return doc.name


def _ensure_oat_check_for_shift(shift):
    check_id = f"OAT-{shift.shift_id}"
    existing = frappe.db.get_value("PMO OAT Check", {"check_id": check_id}, "name")
    if existing:
        return existing
    doc = frappe.get_doc({
        "doctype": "PMO OAT Check",
        "check_id": check_id,
        "project": shift.project,
        "area": "Shift",
        "check": f"OAT for shift {shift.shift_id}: {shift.title}",
        "acceptance_criteria": shift.description or "",
    })
    doc.insert(ignore_permissions=False)
    return doc.name
