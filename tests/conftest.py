import time
import pytest
from utils.driver_factory import create_driver

FB_PKG = "com.facebook.katana"


@pytest.fixture(scope="module")
def driver():
    """
    Driver de Appium con scope de módulo: se crea UNA sola sesión por
    archivo de test y se reutiliza en todos sus casos. Esto reduce las
    reconexiones ADB que causan errores intermitentes de setup.
    """
    _driver = create_driver()
    yield _driver
    _driver.quit()


@pytest.fixture(autouse=True)
def restart_app_after_test(driver):
    """
    Reinicia Facebook al finalizar cada test para limpiar el back stack.
    Los sleeps entre terminate y activate dan tiempo a UiAutomator2 para
    estabilizarse antes del siguiente test, evitando el crash por doble-restart
    rápido que ocurría sin pausas.
    """
    yield
    try:
        driver.terminate_app(FB_PKG)
    except Exception:
        pass
    time.sleep(3)
    try:
        driver.activate_app(FB_PKG)
    except Exception:
        pass
    time.sleep(5)
