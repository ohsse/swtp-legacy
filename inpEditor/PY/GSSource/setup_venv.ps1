# =============================================================================
# setup_venv.ps1  —  가상환경 생성 및 패키지 설치 스크립트
# 실행 방법: 이 파일이 있는 폴더에서 PowerShell 열고
#            .\setup_venv.ps1
# =============================================================================

$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvDir   = Join-Path $ScriptDir '.venv'
$ReqFile   = Join-Path $ScriptDir 'requirements.txt'

Write-Host ""
Write-Host "======================================================"
Write-Host "  가상환경 설정 시작"
Write-Host "  경로: $VenvDir"
Write-Host "======================================================"
Write-Host ""

# ------------------------------------------------------------------
# 1. Python 버전 확인
# ------------------------------------------------------------------
try {
    $pyVer = python --version 2>&1
    Write-Host "[1/4] Python 확인: $pyVer"
} catch {
    Write-Error "Python 이 설치되어 있지 않거나 PATH 에 없습니다."
    exit 1
}

# ------------------------------------------------------------------
# 2. 가상환경 생성 (이미 존재하면 건너뜀)
# ------------------------------------------------------------------
if (Test-Path $VenvDir) {
    Write-Host "[2/4] 가상환경 이미 존재 — 건너뜀 ($VenvDir)"
} else {
    Write-Host "[2/4] 가상환경 생성 중..."
    python -m venv $VenvDir
    Write-Host "      완료: $VenvDir"
}

# ------------------------------------------------------------------
# 3. pip 업그레이드
# ------------------------------------------------------------------
Write-Host "[3/4] pip 업그레이드 중..."
& "$VenvDir\Scripts\python.exe" -m pip install --upgrade pip --quiet
Write-Host "      완료"

# ------------------------------------------------------------------
# 4. requirements.txt 패키지 설치
# ------------------------------------------------------------------
Write-Host "[4/4] 패키지 설치 중 (requirements.txt)..."
Write-Host ""
& "$VenvDir\Scripts\pip.exe" install -r $ReqFile

Write-Host ""
Write-Host "======================================================"
Write-Host "  설치 완료!"
Write-Host ""
Write-Host "  가상환경 활성화 명령:"
Write-Host "    .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "  스크립트 실행 예시:"
Write-Host "    .\.venv\Scripts\python.exe TEST_MAIN_2026_DB.py"
Write-Host "======================================================"
