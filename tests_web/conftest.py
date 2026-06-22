import pytest
from utils.web_driver_factory import create_web_driver


@pytest.fixture(scope="module")
def web_driver():
    """
    Driver de Chrome con emulación móvil, scope de módulo.
    Un browser por archivo de test; se reutiliza en todos los casos del módulo.
    """
    driver = create_web_driver()
    yield driver
    driver.quit()


@pytest.fixture(autouse=True)
def restore_network(web_driver):
    """Garantiza que la red queda habilitada después de cada test."""
    yield
    try:
        web_driver.execute_cdp_cmd("Network.emulateNetworkConditions", {
            "offline": False,
            "latency": 0,
            "downloadThroughput": -1,
            "uploadThroughput": -1,
        })
    except Exception:
        pass
