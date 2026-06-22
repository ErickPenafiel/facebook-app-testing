import json
from pathlib import Path

COOKIE_FILE = Path("tests_web/fb_session.json")


def save_cookies(driver):
    try:
        cookies = driver.get_cookies()
        COOKIE_FILE.write_text(json.dumps(cookies, indent=2))
        print(f"[cookies] Saved {len(cookies)} cookies")
        return True
    except Exception as e:
        print(f"[cookies] Save failed: {e}")
        return False


def load_cookies(driver):
    if not COOKIE_FILE.exists():
        print("[cookies] No saved session file found")
        return False
    try:
        cookies = json.loads(COOKIE_FILE.read_text())
        driver.get("https://m.facebook.com")
        for cookie in cookies:
            cookie.pop("sameSite", None)
            try:
                driver.add_cookie(cookie)
            except Exception:
                pass
        print(f"[cookies] Loaded {len(cookies)} cookies")
        return True
    except Exception as e:
        print(f"[cookies] Load failed: {e}")
        return False
