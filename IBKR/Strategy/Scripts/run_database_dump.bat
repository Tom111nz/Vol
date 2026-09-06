@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM =====================================================
REM MySQL Scheduled Export Script (FINAL / Scheduler-Safe)
REM =====================================================

REM --- Configuration ---
set DB_NAME=vol_test
set EXPORT_DIR=C:\Temp\Vol\dump
set LOG_FILE=%EXPORT_DIR%\vol_test_backup.log

REM --- Full paths (DO NOT QUOTE HERE) ---
set MYSQLDUMP=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe
set POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe
set TAR=%SystemRoot%\System32\tar.exe

REM --- MySQL credentials ---
set MYSQL_USER=backup
set MYSQL_PASS=Bright2

REM --- Retention ---
set KEEP_COUNT=5

REM >>> FIX: Ensure HOME exists for non-interactive MySQL tools
set HOME=%USERPROFILE%

REM =====================================================
REM Ensure export directory exists
REM =====================================================

if not exist "%EXPORT_DIR%" (
    mkdir "%EXPORT_DIR%"
)

REM =====================================================
REM Start log
REM =====================================================

echo ==================================================== >> "%LOG_FILE%"
echo [%date% %time%] Backup started >> "%LOG_FILE%"
whoami >> "%LOG_FILE%"
echo PATH=%PATH% >> "%LOG_FILE%"

REM =====================================================
REM Get timestamp (ROBUST METHOD)
REM =====================================================

for /f "usebackq delims=" %%T in (
    `%POWERSHELL% -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"`
) do set TS=%%T

if not defined TS (
    echo [%date% %time%] ERROR: Timestamp not generated >> "%LOG_FILE%"
    exit /b 1
)

REM --- File names ---
set SQL_FILE=%EXPORT_DIR%\%DB_NAME%_%TS%.sql
set ZIP_FILE=%EXPORT_DIR%\%DB_NAME%_%TS%.zip

echo SQL file: !SQL_FILE! >> "%LOG_FILE%"

REM =====================================================
REM Run mysqldump
REM =====================================================

echo [%date% %time%] Running mysqldump >> "%LOG_FILE%"

"%MYSQLDUMP%" ^
  --host=127.0.0.1 ^
  --protocol=TCP ^
  --user=%MYSQL_USER% ^
  --password=%MYSQL_PASS% ^
  --databases %DB_NAME% ^
  --single-transaction ^
  --routines ^
  --triggers ^
  --events ^
  --no-tablespaces ^
  --add-drop-database ^
  --add-drop-table ^
  --default-character-set=utf8mb4 ^
  --set-gtid-purged=OFF ^
  --column-statistics=0 ^
  --result-file="%SQL_FILE%" ^
  2>>"%LOG_FILE%"

echo [%date% %time%] mysqldump exited with errorlevel %ERRORLEVEL% >> "%LOG_FILE%"

IF ERRORLEVEL 1 (
    echo [%date% %time%] ERROR: mysqldump failed >> "%LOG_FILE%"
    exit /b 1
)

REM =====================================================
REM Verify dump file
REM =====================================================

if not exist "!SQL_FILE!" (
    echo [%date% %time%] ERROR: SQL file not created >> "%LOG_FILE%"
    exit /b 1
)

for %%S in ("!SQL_FILE!") do (
    if %%~zS EQU 0 (
        echo [%date% %time%] ERROR: SQL file is empty >> "%LOG_FILE%"
        exit /b 1
    ) else (
        echo Dump size: %%~zS bytes >> "%LOG_FILE%"
    )
)

REM =====================================================
REM Zip SQL file
REM =====================================================

echo [%date% %time%] Creating ZIP archive >> "%LOG_FILE%"

"%TAR%" -a -c -f "!ZIP_FILE!" -C "%EXPORT_DIR%" "%DB_NAME%_%TS%.sql"

IF ERRORLEVEL 1 (
    echo [%date% %time%] ERROR: ZIP creation failed >> "%LOG_FILE%"
    exit /b 1
)

del /q "!SQL_FILE!"

echo [%date% %time%] ZIP archive completed: !ZIP_FILE! >> "%LOG_FILE%"

REM =====================================================
REM Tuesday-only retention
REM =====================================================

for /f "usebackq delims=" %%D in (
    `%POWERSHELL% -NoProfile -Command "(Get-Date).DayOfWeek"`
) do set DAYNAME=%%D

if /i not "!DAYNAME!"=="Tuesday" (
    echo [%date% %time%] Retention skipped (today is !DAYNAME!) >> "%LOG_FILE%"
    echo [%date% %time%] Backup finished successfully >> "%LOG_FILE%"
    exit /b 0
)

echo [%date% %time%] Applying Tuesday retention (keep %KEEP_COUNT%) >> "%LOG_FILE%"

set COUNT=0

for /f "delims=" %%F in (
    'dir "%EXPORT_DIR%\%DB_NAME%_*.zip" /b /o-d'
) do (
    set /a COUNT+=1
    if !COUNT! GTR %KEEP_COUNT% (
        del /q "%EXPORT_DIR%\%%F"
        echo Deleted old backup: %%F >> "%LOG_FILE%"
    )
)

echo [%date% %time%] Backup finished successfully >> "%LOG_FILE%"
endlocal
exit /b 0