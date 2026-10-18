PIDFILE := .tradutor.pid
LOGFILE := tradutor.log

.PHONY: start stop restart status log

# roda desacoplado do terminal: pode fechar o terminal que continua ligado
start:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "Ja esta ligado (PID $$(cat $(PIDFILE)))"; \
	else \
		setsid nohup python3 -u tradutor.py > $(LOGFILE) 2>&1 & echo $$! > $(PIDFILE); \
		echo "Ligado (PID $$(cat $(PIDFILE)))"; \
	fi

stop:
	@if [ -f $(PIDFILE) ] && kill $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "Desligado"; \
	else \
		echo "Nao estava ligado"; \
	fi
	@rm -f $(PIDFILE)

restart: stop start

status:
	@if [ -f $(PIDFILE) ] && kill -0 $$(cat $(PIDFILE)) 2>/dev/null; then \
		echo "Ligado (PID $$(cat $(PIDFILE)))"; \
	else \
		echo "Desligado"; \
	fi

log:
	@cat $(LOGFILE) 2>/dev/null || echo "Sem log"
