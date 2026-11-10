#!/bin/bash
# Arranca Papel y Luna POS en este computador (backend Django + frontend React).
# Uso: abrir una terminal en esta carpeta y ejecutar:  bash iniciar.sh
# Para detenerlo: Ctrl+C
set -e
RAIZ="$(cd "$(dirname "$0")" && pwd)"

echo "== 1/4 Preparando backend (Python) =="
cd "$RAIZ/backend"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "== 2/4 Creando tablas y usuarios (SQLite local) =="
python manage.py migrate
python manage.py seed_pos

echo "== 3/4 Iniciando API en http://localhost:8000/api/ =="
python manage.py runserver 8000 &
BACKEND_PID=$!
trap 'echo; echo "Deteniendo backend..."; kill $BACKEND_PID 2>/dev/null' EXIT

echo "== 4/4 Preparando e iniciando frontend =="
cd "$RAIZ/frontend"
if [ ! -d node_modules ]; then npm install --no-audit --no-fund; fi
echo
echo "  Abre en el navegador:  http://localhost:5173"
echo "  Administrador: admin / Admin123!"
echo "  Cajero:        cajero / Cajero123!"
echo
npm run dev -- --host localhost --port 5173 --strictPort
