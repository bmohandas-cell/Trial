"""Playwright automation for zipForm Plus — TREC contract filling."""

import os
import time
from playwright.sync_api import sync_playwright, Page, TimeoutError as PWTimeout

ZIPFORM_URL = "https://www.zipformplus.com"
LOGIN_URL = f"{ZIPFORM_URL}/"


def _fill(page: Page, selector: str, value: str, timeout: int = 8000) -> None:
    """Clear and fill a field, skipping if empty value."""
    if not value:
        return
    el = page.wait_for_selector(selector, timeout=timeout)
    el.triple_click()
    el.fill(value)


def _select(page: Page, selector: str, value: str, timeout: int = 8000) -> None:
    if not value:
        return
    page.wait_for_selector(selector, timeout=timeout)
    page.select_option(selector, label=value)


def _click(page: Page, selector: str, timeout: int = 10000) -> None:
    page.wait_for_selector(selector, timeout=timeout)
    page.click(selector)


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

def login(page: Page, email: str, password: str) -> None:
    print("[*] Navigating to zipForm Plus...")
    page.goto(LOGIN_URL, wait_until="networkidle")

    print("[*] Logging in...")
    _fill(page, 'input[name="username"], input[type="email"], #username', email)
    _fill(page, 'input[name="password"], input[type="password"], #password', password)
    _click(page, 'button[type="submit"], input[type="submit"], .login-btn, #loginBtn')
    page.wait_for_load_state("networkidle")
    print("[+] Logged in.")


# ---------------------------------------------------------------------------
# Transaction creation
# ---------------------------------------------------------------------------

def create_transaction(page: Page, name: str) -> None:
    print("[*] Creating new transaction...")
    # Look for a "New Transaction" or "+" button on the dashboard
    _click(page, 'button:has-text("New Transaction"), a:has-text("New Transaction"), [aria-label="New Transaction"], .new-transaction-btn')
    page.wait_for_load_state("networkidle")

    # Name the transaction
    try:
        _fill(page, 'input[placeholder*="transaction" i], input[name*="name" i], #transactionName', name, timeout=5000)
    except PWTimeout:
        pass  # some versions skip this step

    # Select TREC form — One to Four Family Residential
    print("[*] Selecting TREC One-to-Four Family Residential Contract...")
    try:
        _click(page, 'text=One to Four Family Residential', timeout=8000)
    except PWTimeout:
        # Try searching for the form
        try:
            _fill(page, 'input[placeholder*="search" i]', "One to Four Family", timeout=5000)
            time.sleep(1)
            _click(page, 'text=One to Four Family Residential', timeout=8000)
        except PWTimeout:
            print("[!] Could not auto-select form. Please select 'One to Four Family Residential Contract' manually and press Enter.")
            input()

    page.wait_for_load_state("networkidle")
    print("[+] Transaction created.")


# ---------------------------------------------------------------------------
# Field filling — property tab
# ---------------------------------------------------------------------------

def fill_property(page: Page, data: dict) -> None:
    print("[*] Filling property information...")

    field_map = {
        # common zipForm field ids / names for TREC 20-17
        "property_address": [
            '#streetAddress', 'input[name="streetAddress"]',
            'input[placeholder*="Street Address" i]',
        ],
        "property_city": [
            '#city', 'input[name="city"]', 'input[placeholder*="City" i]',
        ],
        "property_county": [
            '#county', 'input[name="county"]', 'input[placeholder*="County" i]',
        ],
        "property_zip": [
            '#zip', 'input[name="zip"]', 'input[placeholder*="Zip" i]',
        ],
        "legal_description": [
            '#legalDescription', 'textarea[name*="legal" i]',
        ],
    }

    for key, selectors in field_map.items():
        value = data.get(key, "")
        if not value:
            continue
        for sel in selectors:
            try:
                _fill(page, sel, value, timeout=3000)
                break
            except PWTimeout:
                continue


def fill_price_and_terms(page: Page, data: dict) -> None:
    print("[*] Filling price and terms...")

    pairs = [
        ("sales_price",   ['#salesPrice',   'input[name*="salesPrice" i]',   'input[placeholder*="Sales Price" i]']),
        ("earnest_money", ['#earnestMoney',  'input[name*="earnestMoney" i]', 'input[placeholder*="Earnest" i]']),
        ("down_payment",  ['#downPayment',   'input[name*="downPayment" i]',  'input[placeholder*="Down Payment" i]']),
        ("loan_amount",   ['#loanAmount',    'input[name*="loanAmount" i]',   'input[placeholder*="Loan Amount" i]']),
        ("loan_years",    ['#loanYears',     'input[name*="loanYears" i]',    'input[placeholder*="Term" i]']),
        ("interest_rate", ['#interestRate',  'input[name*="interestRate" i]', 'input[placeholder*="Interest" i]']),
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

    # Financing type radio/select
    financing = data.get("financing_type", "")
    if financing:
        try:
            page.click(f'label:has-text("{financing}"), input[value*="{financing}" i]', timeout=4000)
        except PWTimeout:
            try:
                _select(page, 'select[name*="financing" i]', financing, timeout=3000)
            except PWTimeout:
                pass


def fill_option_and_closing(page: Page, data: dict) -> None:
    print("[*] Filling option period and closing...")

    pairs = [
        ("option_days",   ['#optionDays',   'input[name*="optionDays" i]',   'input[placeholder*="Option Days" i]']),
        ("option_fee",    ['#optionFee',    'input[name*="optionFee" i]',    'input[placeholder*="Option Fee" i]']),
        ("closing_date",  ['#closingDate',  'input[name*="closingDate" i]',  'input[type="date"]', 'input[placeholder*="Closing Date" i]']),
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

    possession = data.get("possession", "")
    if possession:
        try:
            page.click(f'label:has-text("{possession}")', timeout=4000)
        except PWTimeout:
            pass


def fill_parties(page: Page, data: dict) -> None:
    print("[*] Filling buyer/seller information...")

    pairs = [
        ("buyer_name",        ['#buyerName',    'input[name*="buyerName" i]',    'input[placeholder*="Buyer Name" i]']),
        ("buyer_phone",       ['#buyerPhone',   'input[name*="buyerPhone" i]',   'input[placeholder*="Buyer Phone" i]']),
        ("buyer_email",       ['#buyerEmail',   'input[name*="buyerEmail" i]',   'input[placeholder*="Buyer Email" i]']),
        ("seller_name",       ['#sellerName',   'input[name*="sellerName" i]',   'input[placeholder*="Seller Name" i]']),
        ("seller_phone",      ['#sellerPhone',  'input[name*="sellerPhone" i]',  'input[placeholder*="Seller Phone" i]']),
        ("seller_email",      ['#sellerEmail',  'input[name*="sellerEmail" i]',  'input[placeholder*="Seller Email" i]']),
        ("listing_agent",     ['#listingAgent', 'input[name*="listingAgent" i]', 'input[placeholder*="Listing Agent" i]']),
        ("listing_brokerage", ['#listingBrok',  'input[name*="listingBrok" i]',  'input[placeholder*="Listing Broker" i]']),
        ("buyers_agent",      ['#buyersAgent',  'input[name*="buyersAgent" i]',  'input[placeholder*="Buyer.*Agent" i]']),
        ("buyers_brokerage",  ['#buyersBrok',   'input[name*="buyersBrok" i]',   'input[placeholder*="Buyer.*Broker" i]']),
        ("title_company",     ['#titleCompany', 'input[name*="titleCompany" i]', 'input[placeholder*="Title" i]']),
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


# ---------------------------------------------------------------------------
# Addendum navigation
# ---------------------------------------------------------------------------

def open_addendum(page: Page, form_name: str) -> bool:
    """Navigate to an addendum tab/form within the current transaction."""
    print(f"[*] Opening addendum: {form_name}...")
    try:
        # zipForm Plus typically lists forms in a left sidebar or a forms panel
        _click(page, f'text="{form_name}", [title*="{form_name}"], .form-list-item:has-text("{form_name}")', timeout=6000)
        page.wait_for_load_state("networkidle")
        return True
    except PWTimeout:
        # Try "Add Form" workflow
        try:
            _click(page, 'button:has-text("Add Form"), [aria-label="Add Form"], .add-form-btn', timeout=5000)
            page.wait_for_load_state("networkidle")
            search = page.query_selector('input[placeholder*="search" i]')
            if search:
                search.fill(form_name)
                time.sleep(1)
            _click(page, f'text="{form_name}", li:has-text("{form_name}")', timeout=6000)
            page.wait_for_load_state("networkidle")
            return True
        except PWTimeout:
            print(f"[!] Could not auto-open '{form_name}'. Please open it manually and press Enter.")
            input()
            return True


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_contract(page: Page) -> None:
    print("[*] Saving contract...")
    try:
        _click(page, 'button:has-text("Save"), [aria-label="Save"], #saveBtn', timeout=8000)
        page.wait_for_load_state("networkidle")
        print("[+] Contract saved.")
    except PWTimeout:
        print("[!] Save button not found — please save manually.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run(data: dict, headless: bool = False) -> None:
    email = os.environ.get("ZIPFORM_EMAIL", "")
    password = os.environ.get("ZIPFORM_PASSWORD", "")

    if not email or not password:
        raise SystemExit(
            "Set ZIPFORM_EMAIL and ZIPFORM_PASSWORD in your .env file before running."
        )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=200)
        context = browser.new_context(viewport={"width": 1400, "height": 900})
        page = context.new_page()

        try:
            login(page, email, password)
            create_transaction(page, data["transaction_name"])
            fill_property(page, data)
            fill_price_and_terms(page, data)
            fill_option_and_closing(page, data)
            fill_parties(page, data)
            save_contract(page)
            print("\n[+] Done! Contract is filled and saved in zipForm Plus.")
            input("Press Enter to close the browser...")
        except Exception as exc:
            print(f"\n[!] Error: {exc}")
            input("Press Enter to close the browser (check the page for clues)...")
        finally:
            browser.close()
