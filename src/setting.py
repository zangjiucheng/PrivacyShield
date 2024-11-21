ocr_config = ""  # Default (Suggested)
# ocr_config = r'--psm 4' (Alternative)

# Labels for entity prediction
# Most GLiNER models should work best when entity types are in lower case or title case
sensitive_labels = [
    # Personal Information
    "Name",
    "Address",
    "Phone Number",
    "Email Address",
    "ID Number",
    "Social Security Number",
    "Date of Birth",
    "Bank Account Number",
    "Credit Card Number",
    "Driver's License Number",
    "Passport Number",
    "Medical Record Number",
    "IP Address",
    "Issue Date",

    # Company NDA Information
    "Trade Secret",
    "Financial Information",
    "Business Plan",
    "Product Information",
    "Customer List",
    "Supplier Information",
    "Marketing Strategy",
    "Research and Development",
    "Contract Details",
    "Intellectual Property",
]

debug_flag = False # For development purposes