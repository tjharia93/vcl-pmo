app_name = "vcl_pmo_doctypes"
app_title = "VCL PMO Doctypes"
app_publisher = "Vimit Converters Limited"
app_description = "Custom PMO doctypes and native PMO methods for VCL."
app_email = "it@vcl.local"
app_license = "MIT"

fixtures = [
    {"dt": "Role", "filters": [["role_name", "=", "PMO User"]]},
]

doc_events = {
    "PMO Project": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO Requirement": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO Milestone": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO Task": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO RAID Item": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO UAT Case": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO OAT Check": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO UAT Run": {
        "on_update": [
            "vcl_pmo_doctypes.webhooks.recompute_uat_latest",
            "vcl_pmo_doctypes.webhooks.enqueue_excel_sync",
        ]
    },
    "PMO OAT Run": {
        "on_update": [
            "vcl_pmo_doctypes.webhooks.recompute_oat_latest",
            "vcl_pmo_doctypes.webhooks.enqueue_excel_sync",
        ]
    },
    "PMO Document": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO Plan": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
    "PMO Shift": {"on_update": "vcl_pmo_doctypes.webhooks.enqueue_excel_sync"},
}
