#!/usr/bin/env python3
"""
Teste de fumo do HelpDeskZ — percorre os fluxos principais contra uma instância local.

Uso:
    pip install requests beautifulsoup4
    python3 dev/smoke_test.py [URL_BASE] [UTILIZADOR_STAFF] [PASSWORD_STAFF]

Por omissão: http://localhost:8080 admin admin123
Sai com código 1 se algum passo falhar.
NUNCA correr contra a produção: cria bilhetes e utilizadores.
"""
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")
STAFF_USER = sys.argv[2] if len(sys.argv) > 2 else "admin"
STAFF_PASS = sys.argv[3] if len(sys.argv) > 3 else "admin123"

falhas = 0


def passo(nome, ok, detalhe=""):
    global falhas
    print(("  OK   " if ok else "  FALHA") + f"  {nome}" + (f" — {detalhe}" if detalhe and not ok else ""))
    if not ok:
        falhas += 1


def csrf(html):
    tag = BeautifulSoup(html, "html.parser").find("input", {"name": "csrf_test_name"})
    return tag["value"] if tag else ""


def erros(html):
    soup = BeautifulSoup(html, "html.parser")
    alert = soup.select_one(".alert-danger")
    return alert.get_text(" ", strip=True) if alert else ""


marca = str(int(time.time()))

# ---------------------------------------------------------------- Cliente
print("Portal do cliente")
c = requests.Session()
for caminho in ["/", "/search?keyword=teste", "/submit-ticket", "/login", "/forgot-password"]:
    r = c.get(BASE + caminho)
    passo(f"GET {caminho}", r.status_code == 200, f"HTTP {r.status_code}")

r = c.get(BASE + "/submit-ticket")
r = c.post(BASE + "/submit-ticket", data={"csrf_test_name": csrf(r.text), "do": "submit", "department": "1"})
form_url = r.url
passo("Escolher departamento", "/submit-ticket/1" in form_url, form_url)

email_cliente = f"cliente{marca}@example.test"
assunto = f"Bilhete de teste {marca}"
r = c.post(
    form_url,
    data={
        "csrf_test_name": csrf(r.text),
        "do": "submit",
        "fullname": "Cliente Teste",
        "email": email_cliente,
        "subject": assunto,
        "message": "Mensagem com <b>HTML</b> & acentuação: ção.",
    },
    # campo de ficheiro vazio, como um browser envia quando não há anexo
    files={"attachment[]": ("", b"", "application/octet-stream")},
)
passo("Criar bilhete", "/submit-ticket/confirmation/" in r.url, erros(r.text) or r.url)
m = re.search(r"/confirmation/(\d+)/", r.url)
ticket_id = m.group(1) if m else None

# ---------------------------------------------------------------- Staff
print("Painel de staff")
s = requests.Session()
r = s.get(BASE + "/staff/login")
r = s.post(BASE + "/staff/login", data={"csrf_test_name": csrf(r.text), "do": "login",
                                        "username": STAFF_USER, "password": STAFF_PASS})
passo("Login de staff", "/staff/login" not in r.url, erros(r.text))

r = s.get(BASE + "/staff/tickets")
passo("Lista de bilhetes mostra o novo bilhete", assunto in r.text)

if ticket_id:
    r = s.get(f"{BASE}/staff/tickets/view/{ticket_id}")
    passo("Abrir bilhete", r.status_code == 200 and assunto in r.text)
    passo("Mensagem do cliente aparece escapada", "&lt;b&gt;HTML&lt;/b&gt;" in r.text)
    r = s.post(f"{BASE}/staff/tickets/view/{ticket_id}", data={
        "csrf_test_name": csrf(r.text), "do": "reply",
        "message": f"<p>Resposta do staff {marca}</p>", "status": "2",
    }, files={"attachment[]": ("", b"", "application/octet-stream")})
    passo("Responder ao bilhete", f"Resposta do staff {marca}" in s.get(f"{BASE}/staff/tickets/view/{ticket_id}").text,
          erros(r.text))

for caminho in ["/staff/users", "/staff/departments", "/staff/setup/general", "/staff/kb/articles"]:
    r = s.get(BASE + caminho)
    passo(f"GET {caminho}", r.status_code == 200 and "/staff/login" not in r.url, f"HTTP {r.status_code}")

# ---------------------------------------------------------------- Acessos proibidos
print("Proteções")
for caminho in ["/hdz/app/Config/Helpdesk.php", "/hdz/writable/logs/", "/hdz/app/Controllers/Install.php"]:
    r = requests.get(BASE + caminho, allow_redirects=False)
    passo(f"Bloqueado {caminho}", r.status_code in (403, 404), f"HTTP {r.status_code}")

print()
print("RESULTADO:", "tudo OK" if falhas == 0 else f"{falhas} falha(s)")
sys.exit(1 if falhas else 0)
