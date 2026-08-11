Write-Host "Starting DUSON Invitation..."
docker compose up -d --build
docker compose ps
Write-Host ""
Write-Host "Website: http://localhost:8000"
Write-Host "Admin:   http://localhost:8000/admin"
