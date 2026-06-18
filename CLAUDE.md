# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Install dependencies:**
```bash
uv sync
```

**Run all auth tests:**
```bash
pytest tests/test_auth.py -v
```

**Run a single test:**
```bash
pytest tests/test_auth.py::test_tc_auth_001_login_valid -v
```

**Run by marker:**
```bash
pytest -m auth -v
pytest -m messaging -v
pytest -m notifications -v
```

**Run with HTML report:**
```bash
pytest tests/test_auth.py -v --html=reports/report.html
```

**Prerequisites before running any test:**
1. Android device connected (physical or emulator) with `DEVICE_NAME` set in `.env`
2. Appium Server 2.x running: `appium`
3. UiAutomator2 driver installed in Appium

## Architecture

### Page Object Model

All page interactions go through classes in `pages/`:

- `BasePage` — core Appium helpers used by all page classes: element waits, tap by text/description, type into EditText (with multi-strategy fallback), scroll, keyboard dismissal, screenshot/page-source capture for debug.
- `LoginPage(BasePage)` — login form, logout flow, recovery navigation, `is_logged_in()` detection. Contains `_dismiss_gm_popup_if_present()` to handle Android's Google Password Manager popups that intercept EditText focus.
- `MessengerPage(BasePage)` — Messenger navigation, conversation search/open, message sending, delivery status detection.
- `NotificationsPage(BasePage)` — notifications tab navigation.

### Driver factory

`utils/driver_factory.py` creates the Appium WebDriver from `.env` variables, with 3-retry logic. Key capabilities set: `no_reset=True` (preserve FB session between tests), `adbExecTimeout=90000` (tolerates slow devices and the ADB exit-code-255 bug when >255 processes).

Appium server is expected at `http://127.0.0.1:4723`.

### Fixtures and scoping

Two `conftest.py` files exist:
- Root `conftest.py` — function-scoped `driver` fixture (one Appium session per test function).
- `tests/conftest.py` — **module-scoped** `driver` fixture (one session shared across all tests in a file). Tests import this by being in the `tests/` directory. This is the active fixture used by tests to reduce ADB reconnections.

The `restart_app_after_test` autouse fixture (in `tests/conftest.py`) terminates and re-activates Facebook after every test with 3 s + 5 s sleeps to let UiAutomator2 stabilize before the next test starts.

### Test helpers in `tests/test_auth.py`

The auth test file contains a set of module-level helper functions that manage Facebook's complex navigation states:

- `ensure_logged_out(login_page)` — navigates to the raw login form, handling up to 3 iterations of modal dismissal and logout.
- `ensure_logged_in(login_page)` — ensures an active session, calling login if needed.
- `wait_for_login_result(login_page)` — polls for `logged_in | helper_modal | error_modal | timeout`.
- `_dismiss_all_modals(login_page)` — clears the ordered sequence of optional screens FB may show: logout confirmation dialog → save-login dialog → "iniciar sesión en otra cuenta" screen (v1 and v2) → Google Password Manager.

These helpers are duplicated in `tests/test_messaging.py` — if refactoring, extract them to a shared `tests/helpers.py`.

### MessengerPage — UiAutomator2 query budget

Each method is designed to minimise the number of accessibility tree queries sent to UiAutomator2, because the instrumentation process crashes under heavy query load (observed at ~100+ rapid queries). The design rule is **one combined XPATH per decision point**:

- `open_messenger()` — single XPATH with all tab labels/descs joined by `or` (was 10 separate queries)
- `is_messenger_open()` — single XPATH (was 6 queries)
- `wait_for_chat_list()` — calls `is_messenger_open()` every 2 s (was every 1 s)
- `open_conversation()` — `wait_for_element` (presence, not clickable) + `driver.tap([(x,y)])` — avoids the clickability check that times out on FB's non-clickable ViewGroup children
- `send_message()` — `find_elements("Enviar")` + position filter (y > 85% of screen height) — avoids tapping "Reintentar" buttons of previously failed messages; removed the expensive fallback that called `e.rect` on every clickable element
- `get_message_status()` — single combined XPATH poll every 2 s (was 8 texts × 2 methods × N seconds = up to 240 queries)
- `is_in_conversation()` — single XPATH (was 7 hints × 2 methods = 14 queries)
- `is_pending_or_failed_visible()` — single combined XPATH poll (was 7 texts × N seconds)

### Known Facebook UI quirks

- **Google Password Manager interference**: Android's autofill system shows a bottom-sheet or inline dropdown picker when EditText fields get focus, which hides the FB EditText nodes from UiAutomator2. Must be dismissed before interacting with inputs.
- **`tap_by_text_force`**: Some FB buttons have `enabled=false` in the accessibility tree but UiAutomator2 can still tap them. Use this method instead of `tap_by_text` for such elements (e.g., "SALIR", "AHORA NO" dialog buttons).
- **StaleElementReferenceException on password field**: The autofill picker refreshes the view tree after `click()`. The password input must be found, clicked, dismissed, then re-found before `send_keys`.
- **`type_by_edittext_index`** is the reliable fallback for input fields when content-desc/text locators fail — it uses `UiSelector().instance()` which searches across all accessibility windows including system popups.
- **Non-clickable conversation items**: FB chat list items are `Button` (clickable) wrapping `ViewGroup` children whose text/desc UiAutomator2 surfaces. `tap_by_text`/`tap_by_description_contains` (which call `wait_for_clickable`) time out on these children. Fix: use `wait_for_element` (presence) + `driver.tap([(x,y)])` at the element's center coordinates.
- **WiFi ADB stability**: TC_FB_MSG_005 (no-network test) disables WiFi, which drops the ADB connection — the test auto-skips when the device is connected via ADB WiFi. Use USB ADB to run this test reliably.

### Device connection

`DEVICE_NAME` in `.env` must match the ADB device identifier exactly:
- USB: use the short serial from `adb devices` (e.g. `2ab3c7de`)
- WiFi (Android 11+ mDNS): use the full mDNS ID (e.g. `adb-2ab3c7de-XXXXXX._adb-tls-connect._tcp`)

### Evidence and debug artifacts

During test runs, `LoginPage` automatically saves screenshots and XML page sources to `reports/screenshots/`. The `.xml` dump files at the project root (e.g., `login.xml`, `main_fb.xml`) are manually captured page sources used for locator research — not test artifacts.
