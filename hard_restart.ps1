# Set project path
$ProjectPath = "c:\Users\Igors\Desktop\antigravity gatavi projekti\invoice exe"

# Close any existing instances of the app
# Close any existing instances of the app
Write-Host "Killing old processes..." -ForegroundColor Yellow
Stop-Process -Name "InvoiceManager" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "python" -Force -ErrorAction SilentlyContinue
Stop-Process -Name "uvicorn" -Force -ErrorAction SilentlyContinue

# Clear pycache
Get-ChildItem -Path "$ProjectPath" -Include __pycache__ -Recurse | Remove-Item -Recurse -Force

# Start the app
Write-Host "Restarting application..." -ForegroundColor Green
Set-Location -Path "$ProjectPath"
python launcher.py

Write-Host "Press Enter to exit..."
Read-Host
