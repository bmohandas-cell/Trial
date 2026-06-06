"""
TREC Addendum for Property Subject to Mandatory Membership in HOA (Form 36-9)
Automates filling the HOA addendum inside zipForm Plus.
"""

from playwright.sync_api import Page, TimeoutError as PWTimeout


FORM_NAME = "Addendum for Property Subject to Mandatory Membership in a Property Owners Association"


def collect_data() -> dict:
    print("\n-- HOA Addendum (TREC 36-9) --")
    from prompts import ask, ask_choice

    data: dict = {}

    data["hoa_name"] = ask("HOA / Property Owners Association name")
    data["management_company"] = ask("Management company name", required=False)
    data["management_phone"] = ask("Management company phone", required=False)

    data["transfer_fee"] = ask("Transfer fee amount", required=False)
    data["other_fees"] = ask("Other fees description", required=False)

    data["dues_frequency"] = ask_choice(
        "Dues payment frequency",
        ["Monthly", "Quarterly", "Annually", "Other"],
    )
    data["dues_amount"] = ask("Dues amount")

    data["resale_cert"] = ask_choice(
        "Resale certificate — who orders?",
        ["Seller", "Buyer"],
    )
    data["resale_cert_days"] = ask("Days for seller to deliver resale certificate", default="7")

    data["subdivision_info"] = ask_choice(
        "Subdivision information — who orders?",
        ["Seller", "Buyer"],
    )

    data["hoa_approval"] = ask_choice(
        "Does HOA have right to approve buyer?",
        ["Yes", "No"],
    )

    if data["hoa_approval"] == "Yes":
        data["hoa_approval_days"] = ask("HOA approval deadline (days)", default="10")

    data["special_provisions"] = ask("Special provisions / notes", required=False)

    return data


def fill(page: Page, data: dict) -> None:
    """Fill the HOA Addendum already open in the page."""
    print("[*] Filling HOA Addendum...")

    from zipform_bot import _fill, _click

    pairs = [
        ("hoa_name",            ['input[name*="hoaName" i]',          '#hoaName',          'input[placeholder*="Association Name" i]']),
        ("management_company",  ['input[name*="managementCo" i]',     '#managementCompany','input[placeholder*="Management" i]']),
        ("management_phone",    ['input[name*="managementPhone" i]',  '#managementPhone']),
        ("transfer_fee",        ['input[name*="transferFee" i]',      '#transferFee',      'input[placeholder*="Transfer Fee" i]']),
        ("other_fees",          ['input[name*="otherFees" i]',        'textarea[name*="otherFees" i]']),
        ("dues_amount",         ['input[name*="duesAmount" i]',       '#duesAmount',       'input[placeholder*="Dues" i]']),
        ("resale_cert_days",    ['input[name*="resaleCertDays" i]',   '#resaleCertDays']),
        ("hoa_approval_days",   ['input[name*="hoaApprovalDays" i]',  '#hoaApprovalDays']),
        ("special_provisions",  ['textarea[name*="specialProv" i]',   '#specialProvisions']),
    ]

    for key, selectors in pairs:
        value = data.get(key, "")
        if not value:
            continue
        for sel in selectors:
            try:
                _fill(page, sel, value, timeout=3000)
                break
            except PWTimeout:
                continue

    # Dues frequency radio/select
    freq = data.get("dues_frequency", "")
    if freq:
        try:
            page.click(f'label:has-text("{freq}")', timeout=3000)
        except PWTimeout:
            pass

    # Resale cert — who orders radio
    cert = data.get("resale_cert", "")
    if cert:
        try:
            page.click(f'label:has-text("{cert}") >> nth=0', timeout=3000)
        except PWTimeout:
            pass

    # Subdivision info radio
    sub_info = data.get("subdivision_info", "")
    if sub_info:
        try:
            page.click(f'label:has-text("{sub_info}") >> nth=1', timeout=3000)
        except PWTimeout:
            pass

    # HOA approval right
    hoa_approval = data.get("hoa_approval", "")
    if hoa_approval:
        try:
            page.click(f'label:has-text("{hoa_approval}") >> nth=2', timeout=3000)
        except PWTimeout:
            pass

    print("[+] HOA Addendum filled.")
