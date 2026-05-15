cd D:\pos7
:loop
python -m uvicorn gateway_mvp:app --host 0.0.0.0 --port 8443 --ssl-keyfile D:\pos7\certs\key.pem --ssl-certfile D:\pos7\certs\cert.pem
echo Gateway crashed, restarting in 5 seconds...
timeout /t 5
goto loop
