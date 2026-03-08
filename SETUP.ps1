# FuelMaster - Instalador
# Technological Imperius

$BASE = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = "$BASE\venv"

Write-Host ""
Write-Host "=== FuelMaster - Instalador ===" -ForegroundColor Cyan
Write-Host "Carpeta: $BASE" -ForegroundColor Gray
Write-Host ""

# Crear carpetas
Write-Host "[1/5] Creando carpetas..." -ForegroundColor Cyan
foreach ($d in @("static","static\css","static\js","templates","database")) {
    $full = Join-Path $BASE $d
    if (-not (Test-Path $full)) {
        New-Item -ItemType Directory -Path $full -Force | Out-Null
    }
}
Write-Host "      OK" -ForegroundColor Green

# Verificar Python
Write-Host "[2/5] Verificando Python..." -ForegroundColor Cyan
try {
    $pyVer = python --version 2>&1
    Write-Host "      OK: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "      ERROR: Instala Python desde https://python.org" -ForegroundColor Red
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Entorno virtual
Write-Host "[3/5] Entorno virtual..." -ForegroundColor Cyan
if (-not (Test-Path $venv)) {
    python -m venv $venv | Out-Null
    Write-Host "      OK: Creado" -ForegroundColor Green
} else {
    Write-Host "      OK: Ya existe" -ForegroundColor Yellow
}

# Instalar dependencias
Write-Host "[4/5] Instalando Flask y werkzeug..." -ForegroundColor Cyan
& "$venv\Scripts\pip.exe" install flask werkzeug --quiet
Write-Host "      OK" -ForegroundColor Green

# Base de datos
Write-Host "[5/5] Inicializando base de datos..." -ForegroundColor Cyan
Set-Location $BASE
& "$venv\Scripts\python.exe" -c "from database.db_init import init_db; init_db(); print('      OK: Base de datos lista')"

# Crear INICIAR.bat
$bat = "$BASE\INICIAR.bat"
$batContent = "@echo off`r`ntitle FuelMaster`r`ncd /d `"$BASE`"`r`necho.`r`necho  FuelMaster - Technological Imperius`r`necho  Abre: http://localhost:5000`r`necho.`r`ncall venv\Scripts\activate.bat`r`npython app.py`r`npause`r`n"
[System.IO.File]::WriteAllText($bat, $batContent, [System.Text.Encoding]::ASCII)
Write-Host "      OK: INICIAR.bat creado" -ForegroundColor Green

Write-Host ""
Write-Host "=== Instalacion completada ===" -ForegroundColor Green
Write-Host ""
Write-Host "Usuarios del sistema:" -ForegroundColor Yellow
Write-Host "  admin_ti    / TI@Admin2024!  -> Administrador" -ForegroundColor White
Write-Host "  supervisor1 / Super1@2024    -> Supervisor" -ForegroundColor White
Write-Host "  supervisor2 / Super2@2024    -> Supervisor" -ForegroundColor White
Write-Host ""
Write-Host "-> Doble clic en INICIAR.bat" -ForegroundColor Cyan
Write-Host "-> Abre en el navegador: http://localhost:5000" -ForegroundColor Cyan
Write-Host ""
Read-Host "Presiona Enter para cerrar"
