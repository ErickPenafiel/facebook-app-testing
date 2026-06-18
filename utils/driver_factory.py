import os
import time
from dotenv import load_dotenv
from appium import webdriver
from appium.options.android import UiAutomator2Options

load_dotenv()


def create_driver(no_reset=True, max_retries=3):
    options = UiAutomator2Options()
    options.platform_name = os.getenv("PLATFORM_NAME", "Android")
    options.device_name = os.getenv("DEVICE_NAME", "emulator-5554")
    options.automation_name = "UiAutomator2"

    options.app_package = os.getenv("APP_PACKAGE", "com.facebook.katana")
    options.app_activity = os.getenv("APP_ACTIVITY")

    options.no_reset = no_reset
    options.new_command_timeout = 300
    options.set_capability("ignoreHiddenApiPolicyError", True)
    options.set_capability("skipUnlock", True)
    options.set_capability("skipAppInstallGrant", True)
    # Aumentar timeouts de ADB para tolerar dispositivos lentos o el error
    # de exit-code 255 en `adb shell ps -A` (ocurre cuando el dispositivo
    # tiene más de 255 procesos y ps retorna el conteo como exit code).
    options.set_capability("adbExecTimeout", 90000)
    options.set_capability("uiautomator2ServerInstallTimeout", 60000)
    options.set_capability("uiautomator2ServerLaunchTimeout", 60000)

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            driver = webdriver.Remote(
                command_executor="http://127.0.0.1:4723",
                options=options,
            )
            driver.implicitly_wait(5)
            return driver
        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                print(
                    f"\n[driver_factory] Intento {attempt}/{max_retries} "
                    f"fallido: {exc}\nReintentando en 5 s..."
                )
                time.sleep(5)

    raise Exception(
        f"No se pudo crear el driver de Appium después de {max_retries} "
        f"intentos. Último error: {last_error}"
    ) from last_error
