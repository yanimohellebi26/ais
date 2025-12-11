param(
    [string]$FilePath
)

if (-Not (Test-Path $FilePath)) {
    Write-Host "Le fichier '$FilePath' est introuvable."
    exit 1
}

Get-Content $FilePath | docker exec -i ais-db psql -U postgres -d ais
