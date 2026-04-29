$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 main.py dev @args
    exit $LASTEXITCODE
}

& python main.py dev @args
exit $LASTEXITCODE
