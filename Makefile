SHELL := bash

.DEFAULT_GOAL := help

.PHONY: help doctor setup run test clean

help:
	@echo "Comandos disponibles:"
	@echo "  make doctor  - valida Python, tkinter y pygame"
	@echo "  make setup   - crea el entorno e instala dependencias"
	@echo "  make run     - instala lo necesario y ejecuta la aplicacion"
	@echo "  make test    - valida el proyecto y corre pruebas no graficas"
	@echo "  make clean   - elimina los entornos virtuales generados"

doctor:
	@bash scripts/doctor.sh

setup:
	@bash scripts/setup.sh

run:
	@bash scripts/run.sh

test:
	@bash scripts/test.sh

clean:
	@python3 scripts/bootstrap.py clean 2>/dev/null || python scripts/bootstrap.py clean
