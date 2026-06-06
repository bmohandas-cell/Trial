"""Playwright automation for zipForm Plus — TREC contract filling."""

import json
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, ElementHandle, TimeoutError as PWTimeout

ZIPFORM_URL = "https://www.zipformplus.com"
LOGIN_URL = f"{ZIPFORM_URL}/"

# Persisted selector overrides — learned during debug sessions
SELECTOR_CACHE_FILE = Path(__file__).parent / ".selector_cache.json"

# Set to True globally when the user passes --debug
DEBUG_MODE = False


# ---------------------------------------------------------------------------
# Selector cache — persist corrections across runs
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if SELECTOR_CACHE_FILE.exists():
        try:
            return json.loads(SELECTOR_CACHE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_cache(cache: dict) -> None:
    SELECTOR_CACHE_FILE.write_text(json.dumps(cache, indent=2))


_CACHE: dict = _load_cache()


# ---------------------------------------------------------------------------
# Debug helper
# ---------------------------------------------------------------------------

_HIGHLIGHT_JS = """
(selector) => {
    // Remove any previous highlights
    document.querySelectorAll('.__dbg_highlight').forEach(el => {
        el.style.outline = el.dataset.origOutline || '';
        el.classList.remove('__dbg_highlight');
    });
    // Highlight all inputs/selects/textareas to help user identify the field
    document.querySelectorAll('input, select, textarea').forEach(el => {
        el.dataset.origOutline = el.style.outline;
        el.style.outline = '2px dashed #888';
        el.classList.add('__dbg_highlight');
    });
    // If selector given, highlight it in red
    if (selector) {
        try {
            const el = document.querySelector(selector);
            if (el) {
                el.style.outline = '3px solid red';
                el.scrollIntoView({block: 'center'});
            }
        } catch(e) {}
    }
}
"""

_CLEAR_HIGHLIGHT_JS = """
() => {
    document.querySelectorAll('.__dbg_highlight').forEach(el => {
        el.style.outline = el.dataset.origOutline || '';
        el.classList.remove('__dbg_highlight');
    });
}
"""

_DUMP_INPUTS_JS = """
() => {
    const results = [];
    document.querySelectorAll('input, select, textarea').forEach((el, i) => {
        const label = el.labels?.[0]?.innerText?.trim()
            || el.placeholder
            || el.getAttribute('aria-label')
            || el.name
            || el.id
            || '(no label)';
        results.push({
            index: i,
            tag: el.tagName.toLowerCase(),
            id: el.id || null,
            name: el.name || null,
            placeholder: el.placeholder || null,
            type: el.type || null,
            label,
        });
    });
    return results;
}
"""


def _debug_pause(page: Page, field_key: str, value: str) -> str | None:
    """
    Called when all selectors for a field failed in debug mode.
    Shows all inputs on screen, lets user pick one or type a selector.
    Returns the correct selector string, or None to skip the field.
    Saves the answer to the cache.
    """
    print(f"\n{'='*60}")
    print(f"[DEBUG] Could not find field: '{field_key}'  (value to fill: '{value}')")
    print("  All form inputs are now highlighted (dashed border) in the browser.")
    print("  The following inputs were found on the page:\n")

    # Highlight all inputs
    page.evaluate(_HIGHLIGHT_JS, None)

    # Dump a readable list
    inputs: list[dict] = page.evaluate(_DUMP_INPUTS_JS)
    for item in inputs:
        parts = []
        if item["id"]:
            parts.append(f"id='{item['id']}'")
        if item["name"]:
            parts.append(f"name='{item['name']}'")
        if item["placeholder"]:
            parts.append(f"placeholder='{item['placeholder']}'")
        print(f"  [{item['index']:>3}] <{item['tag']}> {item['label']!r:<30}  {', '.join(parts)}")

    print()
    print("Options:")
    print("  • Type a number to use that input (e.g.  5)")
    print("  • Type a CSS selector to try (e.g.  #buyerName)")
    print("  • Press Enter to skip this field")
    print("  • Type 'q' to quit automation")

    raw = input("\n  Your choice: ").strip()

    # Clear highlights
    page.evaluate(_CLEAR_HIGHLIGHT_JS)

    if not raw:
        print(f"  [~] Skipping '{field_key}'")
        return None
    if raw.lower() == "q":
        raise SystemExit("Aborted by user in debug mode.")

    # Numeric index → build selector from id or name
    if raw.isdigit():
        idx = int(raw)
        if 0 <= idx < len(inputs):
            item = inputs[idx]
            if item["id"]:
                sel = f"#{item['id']}"
            elif item["name"]:
                sel = f'[name="{item["name"]}"]'
            else:
                sel = f'{item["tag"]}:nth-of-type({idx + 1})'
        else:
            print("  [!] Index out of range, skipping.")
            return None
    else:
        sel = raw

    # Highlight the chosen selector so user can confirm
    page.evaluate(_HIGHLIGHT_JS, sel)
    confirm = input(f"  Use selector '{sel}' for '{field_key}'? Save to cache? [Y/n]: ").strip().lower()
    page.evaluate(_CLEAR_HIGHLIGHT_JS)

    if confirm == "n":
        return None

    # Persist
    _CACHE[field_key] = sel
    _save_cache(_CACHE)
    print(f"  [+] Saved to .selector_cache.json")
    return sel


# ---------------------------------------------------------------------------
# Core fill/click helpers (debug-aware)
# ---------------------------------------------------------------------------

def _try_selectors(page: Page, selectors: list[str], timeout: int = 3000) -> ElementHandle | None:
    """Try a list of selectors, return the first match or None."""
    for sel in selectors:
        try:
            el = page.wait_for_selector(sel, timeout=timeout)
            if el:
                return el
        except PWTimeout:
            continue
    return None


def _fill(page: Page, selector: str, value: str, timeout: int = 8000) -> None:
    """Clear and fill a single selector (non-debug path)."""
    if not value:
        return
    el = page.wait_for_selector(selector, timeout=timeout)
    el.triple_click()
    el.fill(value)


def _fill_field(page: Page, field_key: str, selectors: list[str], value: str) -> None:
    """
    Try all selectors for a named field.
    In debug mode, pause and ask the user if nothing matches.
    Uses cached selector if available.
    """
    if not value:
        return

    # Prefer cached override
    effective_selectors = ([_CACHE[field_key]] if field_key in _CACHE else []) + selectors

    el = _try_selectors(page, effective_selectors)
    if el:
        el.triple_click()
        el.fill(value)
        return

    if DEBUG_MODE:
        sel = _debug_pause(page, field_key, value)
        if sel:
            try:
                el = page.wait_for_selector(sel, timeout=5000)
                if el:
                    el.triple_click()
                    el.fill(value)
            except PWTimeout:
                print(f"  [!] Selector '{sel}' still not found after debug — skipping.")
    else:
        print(f"  [~] Could not find field '{field_key}' — skipping. (run with --debug to fix)")


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
    _click(page, 'button:has-text("New Transaction"), a:has-text("New Transaction"), [aria-label="New Transaction"], .new-transaction-btn')
    page.wait_for_load_state("networkidle")

    try:
        _fill(page, 'input[placeholder*="transaction" i], input[name*="name" i], #transactionName', name, timeout=5000)
    except PWTimeout:
        pass

    print("[*] Selecting TREC One-to-Four Family Residential Contract...")
    try:
        _click(page, 'text=One to Four Family Residential', timeout=8000)
    except PWTimeout:
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
# Field filling
# ---------------------------------------------------------------------------

def fill_property(page: Page, data: dict) -> None:
    print("[*] Filling property information...")
    fields = [
        ("property_address", ['#streetAddress', 'input[name="streetAddress"]', 'input[placeholder*="Street Address" i]']),
        ("property_city",    ['#city',          'input[name="city"]',           'input[placeholder*="City" i]']),
        ("property_county",  ['#county',        'input[name="county"]',         'input[placeholder*="County" i]']),
        ("property_zip",     ['#zip',           'input[name="zip"]',            'input[placeholder*="Zip" i]']),
        ("legal_description",['#legalDescription', 'textarea[name*="legal" i]']),
    ]
    for key, selectors in fields:
        _fill_field(page, key, selectors, data.get(key, ""))


def fill_price_and_terms(page: Page, data: dict) -> None:
    print("[*] Filling price and terms...")
    fields = [
        ("sales_price",   ['#salesPrice',   'input[name*="salesPrice" i]',   'input[placeholder*="Sales Price" i]']),
        ("earnest_money", ['#earnestMoney',  'input[name*="earnestMoney" i]', 'input[placeholder*="Earnest" i]']),
        ("down_payment",  ['#downPayment',   'input[name*="downPayment" i]',  'input[placeholder*="Down Payment" i]']),
        ("loan_amount",   ['#loanAmount',    'input[name*="loanAmount" i]',   'input[placeholder*="Loan Amount" i]']),
        ("loan_years",    ['#loanYears',     'input[name*="loanYears" i]',    'input[placeholder*="Term" i]']),
        ("interest_rate", ['#interestRate',  'input[name*="interestRate" i]', 'input[placeholder*="Interest" i]']),
    ]
    for key, selectors in fields:
        _fill_field(page, key, selectors, data.get(key, ""))

    financing = data.get("financing_type", "")
    if financing:
        try:
            page.click(f'label:has-text("{financing}"), input[value*="{financing}" i]', timeout=4000)
        except PWTimeout:
            try:
                _select(page, 'select[name*="financing" i]', financing, timeout=3000)
            except PWTimeout:
                if DEBUG_MODE:
                    _debug_pause(page, "financing_type", financing)


def fill_option_and_closing(page: Page, data: dict) -> None:
    print("[*] Filling option period and closing...")
    fields = [
        ("option_days",  ['#optionDays',  'input[name*="optionDays" i]',  'input[placeholder*="Option Days" i]']),
        ("option_fee",   ['#optionFee',   'input[name*="optionFee" i]',   'input[placeholder*="Option Fee" i]']),
        ("closing_date", ['#closingDate', 'input[name*="closingDate" i]', 'input[type="date"]', 'input[placeholder*="Closing Date" i]']),
    ]
    for key, selectors in fields:
        _fill_field(page, key, selectors, data.get(key, ""))

    possession = data.get("possession", "")
    if possession:
        try:
            page.click(f'label:has-text("{possession}")', timeout=4000)
        except PWTimeout:
            if DEBUG_MODE:
                _debug_pause(page, "possession", possession)


def fill_parties(page: Page, data: dict) -> None:
    print("[*] Filling buyer/seller information...")
    fields = [
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
    for key, selectors in fields:
        _fill_field(page, key, selectors, data.get(key, ""))


# ---------------------------------------------------------------------------
# Addendum navigation
# ---------------------------------------------------------------------------

def open_addendum(page: Page, form_name: str) -> bool:
    print(f"[*] Opening addendum: {form_name}...")
    try:
        _click(page, f'text="{form_name}", [title*="{form_name}"], .form-list-item:has-text("{form_name}")', timeout=6000)
        page.wait_for_load_state("networkidle")
        return True
    except PWTimeout:
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

def run(data: dict, headless: bool = False, debug: bool = False) -> None:
    global DEBUG_MODE
    DEBUG_MODE = debug

    email = os.environ.get("ZIPFORM_EMAIL", "")
    password = os.environ.get("ZIPFORM_PASSWORD", "")

    if not email or not password:
        raise SystemExit("Set ZIPFORM_EMAIL and ZIPFORM_PASSWORD in your .env file before running.")

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
