# Facebook Appium Tests

Suite de pruebas automatizadas para la aplicación móvil de Facebook (Android) desarrollada con **Appium 2.x + Python + pytest**, siguiendo el patrón **Page Object Model (POM)**.

---

## Tabla de contenidos

1. [Requisitos previos](#requisitos-previos)
2. [Instalación](#instalación)
3. [Configuración del entorno](#configuración-del-entorno)
4. [Conexión del dispositivo](#conexión-del-dispositivo)
5. [Ejecutar las pruebas](#ejecutar-las-pruebas)
6. [Casos de prueba](#casos-de-prueba)
   - [Módulo de Autenticación](#módulo-de-autenticación-test_authauthpy)
   - [Módulo de Mensajería](#módulo-de-mensajería-test_messagingpy)
7. [Arquitectura del proyecto](#arquitectura-del-proyecto)
8. [Quirks conocidos de Facebook](#quirks-conocidos-de-facebook)
9. [Evidencias y reportes](#evidencias-y-reportes)

---

## Requisitos previos

| Herramienta | Versión mínima | Instalación |
|-------------|---------------|-------------|
| Python | 3.13+ | [python.org](https://www.python.org) |
| uv (gestor de paquetes) | cualquiera | `pip install uv` |
| Node.js | 18+ | [nodejs.org](https://nodejs.org) |
| Appium Server | 2.x | `npm install -g appium` |
| UiAutomator2 driver | cualquiera | `appium driver install uiautomator2` |
| Android SDK Platform Tools | cualquiera | Android Studio o SDK standalone |

El dispositivo Android debe tener:
- **Opciones de desarrollador** habilitadas
- **Depuración USB** (o **Depuración inalámbrica**) activada
- La aplicación **Facebook** (`com.facebook.katana`) instalada y con una sesión activa

---

## Instalación

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd facebook_appium_tests

# 2. Instalar dependencias Python
uv sync
```

---

## Configuración del entorno

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
PLATFORM_NAME=Android
DEVICE_NAME=<serial_del_dispositivo>

APP_PACKAGE=com.facebook.katana
APP_ACTIVITY=com.facebook.katana.LoginActivity

FB_EMAIL=tu_correo@ejemplo.com
FB_PASSWORD=TuPasswordCorrecto
FB_INVALID_PASSWORD=PasswordIncorrecta123
FB_UNKNOWN_USER=usuario_no_registrado@test.com
FB_CONTACT_NAME=Nombre Apellido del Contacto
FB_RECOVERY_EMAIL=numeroDeRecuperacion
```

> **Nota sobre `DEVICE_NAME`:**
> - Conexión USB: usa el serial de `adb devices` (ej. `2ab3c7de`)
> - Conexión WiFi (Android 11+): usa el ID mDNS de `adb devices` (ej. `adb-2ab3c7de-XXXXXX._adb-tls-connect._tcp`)
> - **Recomendación:** usa conexión WiFi ADB para evitar desconexiones de USB durante suites largas.

---

## Conexión del dispositivo

### USB

```bash
# Conectar el cable, aceptar el diálogo en el teléfono y verificar:
adb devices
# Debe mostrar: <serial>   device
```

### WiFi (Android 11+)

1. En el teléfono: **Ajustes → Opciones de desarrollador → Depuración inalámbrica → Activar**
2. Conecta el dispositivo una primera vez por USB y ejecuta:
   ```bash
   adb tcpip 5555
   ```
3. Desconecta el cable y obtén la IP del teléfono (**Ajustes → Acerca del teléfono**)
4. Conéctate por WiFi:
   ```bash
   adb connect 192.168.X.X:5555
   ```
5. Verifica: `adb devices` debe mostrar `192.168.X.X:5555   device`

---

## Ejecutar las pruebas

**Requisitos antes de correr cualquier test:**

```bash
# Terminal 1: iniciar Appium Server
appium

# Terminal 2: ejecutar tests
```

```bash
# Suite completa de autenticación
uv run pytest tests/test_auth.py -v

# Suite completa de mensajería
uv run pytest tests/test_messaging.py -v

# Test individual
uv run pytest tests/test_auth.py::test_tc_auth_001_login_valid -v
uv run pytest tests/test_messaging.py::test_tc_fb_msg_001_acceso_mensajeria -v

# Por marcador
uv run pytest -m auth -v
uv run pytest -m messaging -v

# Con reporte HTML
uv run pytest tests/test_auth.py -v --html=reports/report_auth.html
uv run pytest tests/test_messaging.py -v --html=reports/report_messaging.html
```

---

## Casos de prueba

### Módulo de Autenticación (`tests/test_auth.py`)

| ID | Nombre | Descripción | Resultado esperado |
|----|--------|-------------|-------------------|
| TC_AUTH_001 | Login con credenciales válidas | Inicia sesión con email y contraseña correctos | Feed de Facebook visible (Inicio / Menú / Buscar) |
| TC_AUTH_002 | Login con contraseña incorrecta | Intenta login con contraseña errónea | Mensaje de error o modal de ayuda visible |
| TC_AUTH_003 | Login con usuario no registrado | Intenta login con email inexistente | Mensaje de error o modal de ayuda visible |
| TC_AUTH_004 | Campos vacíos en login | Envía el formulario sin escribir nada | Validación de campo requerido visible |
| TC_AUTH_005 | Recuperación de cuenta | Navega por el flujo "¿Olvidaste tu contraseña?" | Pantalla "Encuentra tu cuenta" o "Elige tu cuenta" visible |
| TC_AUTH_006 | Cierre de sesión | Cierra la sesión activa desde el menú | Pantalla de login o selector de cuentas visible |
| TC_AUTH_007 | Persistencia de sesión | Cierra y reabre la app sin cerrar sesión | Sesión activa al reabrir (sin pedir login) |

### Módulo de Mensajería (`tests/test_messaging.py`)

| ID | Nombre | Descripción | Resultado esperado |
|----|--------|-------------|-------------------|
| TC_FB_MSG_001 | Acceso al módulo de mensajería | Navega a Messenger desde el feed principal | Bandeja de conversaciones visible |
| TC_FB_MSG_002 | Envío de mensaje de texto | Busca un contacto, abre la conversación y envía un mensaje | El mensaje aparece en el chat |
| TC_FB_MSG_003 | Recepción de mensaje entrante | Abre la bandeja y accede a una conversación existente | Se pueden leer mensajes recibidos |
| TC_FB_MSG_004 | Estado del mensaje enviado | Envía un mensaje y espera confirmación de entrega | Estado "Enviado", "Entregado" o "Visto" visible |
| TC_FB_MSG_005 | Envío sin conexión | Desactiva la red e intenta enviar un mensaje | Estado "Pendiente" o "Error" visible (*) |
| TC_FB_MSG_006 | Búsqueda de conversación | Usa el buscador de Messenger para encontrar un contacto | El contacto aparece en los resultados |
| TC_FB_MSG_007 | Sincronización entre sesiones | Envía un mensaje, reinicia la app y verifica que persiste | El mensaje sigue visible tras reiniciar |

> (*) TC_FB_MSG_005 se omite automáticamente cuando el dispositivo usa ADB WiFi, ya que deshabilitar la red corta la conexión ADB.

---

## Arquitectura del proyecto

```
facebook_appium_tests/
├── pages/
│   ├── base_page.py        # Clase base con helpers: waits, tap, scroll, screenshots
│   ├── login_page.py       # Formulario de login, logout, recuperación, is_logged_in()
│   └── messenger_page.py   # Navegación a Messenger, búsqueda, envío, estados
├── tests/
│   ├── conftest.py         # Fixture de driver (scope=module) + autouse restart_app_after_test
│   ├── test_auth.py        # 7 casos de prueba de autenticación
│   ├── test_messaging.py   # 7 casos de prueba de mensajería
│   └── test_notifications.py
├── utils/
│   └── driver_factory.py   # Crea el WebDriver Appium (3 reintentos, capabilities)
├── reports/
│   └── screenshots/        # Capturas automáticas generadas durante los tests
├── evidence/               # Evidencia manual adicional
├── .env                    # Variables de configuración (no subir al repositorio)
├── pyproject.toml          # Dependencias y configuración de pytest
└── CLAUDE.md               # Instrucciones para el asistente de IA (Claude Code)
```

### Page Object Model

**`BasePage`** — clase raíz usada por todas las páginas:
- `wait_for_element` / `wait_for_clickable` — esperas explícitas
- `tap_by_text` / `tap_by_description_contains` / `tap_by_text_force` — interacción con elementos
- `is_text_visible` / `is_description_visible` — verificaciones de presencia
- `type_by_edittext_index` — escritura en campos de texto (incluye manejo de Google Password Manager)
- `take_screenshot` / `_save_page_source` — artefactos de debug

**`LoginPage(BasePage)`**:
- `login(email, password)` — rellena y envía el formulario de login
- `logout()` — navega al menú y cierra sesión
- `is_logged_in()` — detecta el feed principal de Facebook
- `go_to_recovery()` — navega al flujo de recuperación de contraseña
- `_dismiss_gm_popup_if_present()` — cierra el Google Password Manager antes de escribir en campos

**`MessengerPage(BasePage)`**:
- `open_messenger()` — navega a Messenger desde cualquier pantalla (1 query XPATH)
- `is_messenger_open()` / `wait_for_chat_list()` — verifican la bandeja de conversaciones
- `search_conversation(name)` — usa el buscador de Messenger
- `open_conversation(name)` — abre una conversación por coordenadas (maneja elementos no-clickables)
- `send_message(message)` — escribe y envía; filtra el botón por posición para evitar "Reintentar"
- `get_message_status()` — detecta "Enviado", "Entregado" o "Visto" (1 query XPATH combinada)
- `is_in_conversation()` — verifica que hay un campo de entrada visible

### Fixtures (`tests/conftest.py`)

- **`driver` (scope=module):** una sola sesión Appium por archivo de test, evitando reconexiones ADB costosas entre casos.
- **`restart_app_after_test` (autouse):** cierra y reabre Facebook tras cada test con pausas de 3 s + 5 s para que UiAutomator2 se estabilice.

### Driver factory (`utils/driver_factory.py`)

Crea la sesión Appium con:
- `no_reset=True` — preserva la sesión de Facebook entre tests
- `adbExecTimeout=90000` — tolera dispositivos lentos y el error de exit-code 255 de ADB
- 3 reintentos automáticos con espera de 5 s entre intentos

---

## Quirks conocidos de Facebook

| Problema | Causa | Solución implementada |
|----------|-------|-----------------------|
| Google Password Manager interfiere con los inputs | Android muestra un bottom sheet de autocompletado que oculta los EditText de UiAutomator2 | `_dismiss_gm_popup_if_present()` lo cierra antes de escribir; `type_by_edittext_index` busca en todos los accessibility windows |
| Botón "Enviar" y botón "Reintentar" tienen la misma descripción | Los mensajes fallidos tienen un botón "Reintentar" en el área del chat | `send_message()` filtra por posición Y (solo acepta botones en el 15% inferior de la pantalla) |
| UiAutomator2 se cuelga o crashea con muchas queries | El proceso de instrumentación se agota con >100 queries de accesibilidad rápidas | Todos los métodos usan XPATHs combinados (1 query en lugar de N loops) |
| Elementos con `enabled=false` que sí son tapables | UiAutomator2 reporta algunos botones como no-habilitados aunque respondan al toque | `tap_by_text_force()` usa presencia en lugar de clickabilidad |
| StaleElementReferenceException en el campo de contraseña | El autofill picker refresca el árbol de vistas al hacer `click()` | El campo se busca → click → dismiss picker → re-búsqueda antes de `send_keys` |
| `press_keycode(66)` no envía mensajes en Messenger | Enter en Messenger crea una nueva línea en lugar de enviar | Se usa tap por coordenadas al botón Enviar |

---

## Evidencias y reportes

Durante la ejecución los tests guardan automáticamente:

- **Capturas de pantalla** → `reports/screenshots/<nombre>_<timestamp>.png`
- **Page source XML** → `reports/screenshots/<nombre>_<timestamp>.xml` (solo en errores críticos)

Para generar un reporte HTML completo:

```bash
uv run pytest tests/test_auth.py tests/test_messaging.py -v \
  --html=reports/report_completo.html --self-contained-html
```
