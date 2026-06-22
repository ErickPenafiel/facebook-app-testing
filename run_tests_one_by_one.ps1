# run_tests_one_by_one.ps1
# Ejecuta cada caso de prueba de forma individual para evitar
# el agotamiento de UiAutomator2 que ocurre en suites largas.
# TC_FB_MSG_005 excluido: requiere ADB por USB (incompatible con ADB WiFi).
#
# Uso: .\run_tests_one_by_one.ps1
# Pre-requisito: Appium Server corriendo ("appium" en otra terminal)

$ErrorActionPreference = "Continue"

$passed  = @()
$failed  = @()
$skipped = @()

function Run-Test {
    param([string]$TestId, [string]$Label)

    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  $Label" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan

    $output = uv run pytest $TestId -v 2>&1
    $output | ForEach-Object { Write-Host $_ }

    if ($output -match "1 passed") {
        return "passed"
    } elseif ($output -match "1 skipped") {
        return "skipped"
    } else {
        return "failed"
    }
}

# ---------------------------------------------------------------------------
# AUTENTICACION
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  MODULO: AUTENTICACION" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

$result = Run-Test "tests/test_auth.py::test_tc_auth_001_login_valid" "TC_AUTH_001 - Login con credenciales validas"
if ($result -eq "passed") { $passed += "TC_AUTH_001" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_001" } else { $failed += "TC_AUTH_001" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_002_login_invalid_password" "TC_AUTH_002 - Login con password incorrecto"
if ($result -eq "passed") { $passed += "TC_AUTH_002" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_002" } else { $failed += "TC_AUTH_002" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_003_login_unknown_user" "TC_AUTH_003 - Login con usuario no registrado"
if ($result -eq "passed") { $passed += "TC_AUTH_003" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_003" } else { $failed += "TC_AUTH_003" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_004_empty_fields" "TC_AUTH_004 - Campos vacios"
if ($result -eq "passed") { $passed += "TC_AUTH_004" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_004" } else { $failed += "TC_AUTH_004" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_005_account_recovery" "TC_AUTH_005 - Recuperacion de cuenta"
if ($result -eq "passed") { $passed += "TC_AUTH_005" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_005" } else { $failed += "TC_AUTH_005" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_006_logout" "TC_AUTH_006 - Cierre de sesion"
if ($result -eq "passed") { $passed += "TC_AUTH_006" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_006" } else { $failed += "TC_AUTH_006" }
Start-Sleep -Seconds 5

$result = Run-Test "tests/test_auth.py::test_tc_auth_007_session_persistence" "TC_AUTH_007 - Persistencia de sesion"
if ($result -eq "passed") { $passed += "TC_AUTH_007" } elseif ($result -eq "skipped") { $skipped += "TC_AUTH_007" } else { $failed += "TC_AUTH_007" }
Start-Sleep -Seconds 8

# ---------------------------------------------------------------------------
# MENSAJERIA (sin TC_005 - requiere USB)
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor Yellow
Write-Host "  MODULO: MENSAJERIA (ADB WiFi - TC_005 excluido)" -ForegroundColor Yellow
Write-Host "============================================================" -ForegroundColor Yellow

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_001_acceso_mensajeria" "TC_FB_MSG_001 - Acceso al modulo de mensajeria"
if ($result -eq "passed") { $passed += "TC_FB_MSG_001" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_001" } else { $failed += "TC_FB_MSG_001" }
Start-Sleep -Seconds 8

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_002_envio_mensaje_texto" "TC_FB_MSG_002 - Envio de mensaje de texto"
if ($result -eq "passed") { $passed += "TC_FB_MSG_002" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_002" } else { $failed += "TC_FB_MSG_002" }
Start-Sleep -Seconds 8

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_003_recepcion_mensaje_entrante" "TC_FB_MSG_003 - Recepcion de mensaje entrante"
if ($result -eq "passed") { $passed += "TC_FB_MSG_003" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_003" } else { $failed += "TC_FB_MSG_003" }
Start-Sleep -Seconds 8

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_004_estado_mensaje_enviado" "TC_FB_MSG_004 - Estado del mensaje enviado"
if ($result -eq "passed") { $passed += "TC_FB_MSG_004" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_004" } else { $failed += "TC_FB_MSG_004" }
Start-Sleep -Seconds 8

# TC_FB_MSG_005 - OMITIDO (requiere ADB USB, incompatible con ADB WiFi)
Write-Host ""
Write-Host "  [OMITIDO] TC_FB_MSG_005 - Envio sin conexion (requiere ADB USB)" -ForegroundColor DarkYellow
$skipped += "TC_FB_MSG_005 (ADB USB requerido)"

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_006_busqueda_conversacion" "TC_FB_MSG_006 - Busqueda de conversacion"
if ($result -eq "passed") { $passed += "TC_FB_MSG_006" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_006" } else { $failed += "TC_FB_MSG_006" }
Start-Sleep -Seconds 8

$result = Run-Test "tests/test_messaging.py::test_tc_fb_msg_007_sincronizacion_sesiones" "TC_FB_MSG_007 - Sincronizacion entre sesiones"
if ($result -eq "passed") { $passed += "TC_FB_MSG_007" } elseif ($result -eq "skipped") { $skipped += "TC_FB_MSG_007" } else { $failed += "TC_FB_MSG_007" }

# ---------------------------------------------------------------------------
# RESUMEN
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "============================================================" -ForegroundColor White
Write-Host "  RESUMEN DE EJECUCION" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor White
Write-Host ""
Write-Host "  PASADOS  ($($passed.Count)):" -ForegroundColor Green
$passed  | ForEach-Object { Write-Host "    [OK] $_" -ForegroundColor Green }
Write-Host ""
Write-Host "  OMITIDOS ($($skipped.Count)):" -ForegroundColor Yellow
$skipped | ForEach-Object { Write-Host "    [--] $_" -ForegroundColor Yellow }
Write-Host ""
Write-Host "  FALLIDOS ($($failed.Count)):" -ForegroundColor Red
$failed  | ForEach-Object { Write-Host "    [XX] $_" -ForegroundColor Red }
Write-Host ""

$total = $passed.Count + $failed.Count + $skipped.Count
Write-Host "  Total: $total tests | $($passed.Count) OK | $($failed.Count) FAIL | $($skipped.Count) SKIP" -ForegroundColor White
Write-Host ""
