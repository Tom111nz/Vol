@echo off

echo ====================================== >> C:\Scripts\EoD_Process.log
echo Started %date% %time% >> C:\Scripts\EoD_Process.log

cd /d "C:\Users\Tom\PycharmProjects\Vol"

echo Before Python >> C:\Scripts\EoD_Process.log

"C:\Users\Tom\AppData\Local\Programs\Python\Python314\python.exe" "C:\Users\Tom\PycharmProjects\Vol\IBKR\EoD_Process.py" >> C:\Scripts\EoD_Process.log 2>&1

echo Finished %date% %time% ErrorLevel=%errorlevel% >> C:\Scripts\EoD_Process.log