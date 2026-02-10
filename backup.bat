@echo off
echo --- BACKING UP TO GITHUB ---

:: 1. Stage all new files (The .gitignore keeps the ROMs out)
git add .

:: 2. Save the snapshot with the current time
set "timestamp=%date% %time%"
git commit -m "Stream Backup: %timestamp%"

:: 3. Upload to the cloud
git push origin main

echo.
echo ✅ DONE! Everything is safe on GitHub.
pause