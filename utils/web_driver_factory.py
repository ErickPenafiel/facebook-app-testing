import undetected_chromedriver as uc

MOBILE_UA = (
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Mobile Safari/537.36"
)


def create_web_driver():
    options = uc.ChromeOptions()
    options.add_argument("--lang=es-419")
    options.add_argument("--disable-notifications")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-blink-features=AutomationControlled")
    # Disable WebAuthentication/passkey API so Facebook falls back to password login
    options.add_argument("--disable-features=WebAuthentication")

    driver = uc.Chrome(options=options, version_main=149)

    driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
        "mobile": True,
        "width": 390,
        "height": 844,
        "deviceScaleFactor": 3,
    })
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {
        "userAgent": MOBILE_UA,
        "acceptLanguage": "es-419,es;q=0.9",
    })

    driver.set_page_load_timeout(30)
    return driver
