#!/usr/bin/env python3
"""
Testes de regressão de segurança do HelpDeskZ (fork AESCAS).

Cada teste tenta explorar uma falha corrigida na Fase 1. Se alguma voltar a
aparecer, o teste falha. Precisa de uma instância LOCAL acabada de instalar.

Uso:
    pip install requests beautifulsoup4
    python3 dev/security_test.py [URL_BASE] [ADMIN] [PASSWORD]

Variáveis de ambiente opcionais:
    HDZ_MYSQL  comando para a BD   (omissão: "mysql -uhdz -phdzdev -h127.0.0.1 helpdeskz")
               com Docker:         "docker compose exec -T db mysql -uhdz -phdzdev helpdeskz"
    HDZ_PHP    comando PHP da app  (omissão: "php"; com Docker: "docker compose exec -T app php")

NUNCA correr contra a produção.
"""
import hashlib
import hmac
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")
ADMIN = sys.argv[2] if len(sys.argv) > 2 else "admin"
ADMIN_PASS = sys.argv[3] if len(sys.argv) > 3 else "admin123"
MYSQL = shlex.split(os.environ.get("HDZ_MYSQL", "mysql -uhdz -phdzdev -h127.0.0.1 helpdeskz"))
PHP = shlex.split(os.environ.get("HDZ_PHP", "php"))
ROOT = Path(__file__).resolve().parent.parent
EMPTY_FILE = {"attachment[]": ("", b"", "application/octet-stream")}

XSS = '<img src=x onerror=alert(1)>'
XSS_SCRIPT = '<script>alert(1)</script>'
marca = str(int(time.time()))
falhas = 0


def passo(nome, ok, detalhe=""):
    global falhas
    print(("  OK   " if ok else "  FALHA") + f"  {nome}" + (f" — {detalhe}" if detalhe and not ok else ""))
    if not ok:
        falhas += 1


def sql(query):
    r = subprocess.run(MYSQL + ["-N", "-B", "-e", query], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout.strip()


def csrf(html):
    tag = BeautifulSoup(html, "html.parser").find("input", {"name": "csrf_test_name"})
    return tag["value"] if tag else ""


def sem_xss(html):
    """Verdadeiro se nenhum payload aparece por escapar no HTML."""
    return (re.search(r"<img[^>]*onerror", html, re.I) is None
            and re.search(r"<script[^>]*>\s*alert", html, re.I) is None)


def login_staff(user, password):
    s = requests.Session()
    r = s.get(BASE + "/staff/login")
    s.post(BASE + "/staff/login", data={"csrf_test_name": csrf(r.text), "do": "login",
                                        "username": user, "password": password})
    return s


def criar_bilhete(nome, email, assunto, departamento="1", ficheiro=None):
    c = requests.Session()
    r = c.get(BASE + "/submit-ticket")
    r = c.post(BASE + "/submit-ticket", data={"csrf_test_name": csrf(r.text), "do": "submit", "department": departamento})
    files = {"attachment[]": ficheiro} if ficheiro else EMPTY_FILE
    r = c.post(r.url, data={"csrf_test_name": csrf(r.text), "do": "submit", "fullname": nome,
                            "email": email, "subject": assunto, "message": "Teste"}, files=files)
    m = re.search(r"/confirmation/(\d+)/", r.url)
    return m.group(1) if m else None


admin = login_staff(ADMIN, ADMIN_PASS)

# ------------------------------------------------------------------ XSS
print("XSS persistente")
tid = criar_bilhete(f"Nome {XSS}", f"xss{marca}@example.test", f"Assunto {XSS_SCRIPT} {XSS}")
passo("Bilhete com payload criado", tid is not None)
r = admin.get(BASE + "/staff/tickets")
passo("Lista de bilhetes (staff) escapa assunto e nome", sem_xss(r.text))
r = admin.get(f"{BASE}/staff/tickets/view/{tid}")
passo("Vista do bilhete (staff) escapa nome e assunto", sem_xss(r.text))

r = admin.post(f"{BASE}/staff/tickets/view/{tid}", data={
    "csrf_test_name": csrf(r.text), "do": "reply", "status": "1",
    "message": f"<p>ok{marca}</p>{XSS_SCRIPT}<a href=\"javascript:alert(1)\">x</a>"}, files=EMPTY_FILE)
r = admin.get(f"{BASE}/staff/tickets/view/{tid}")
passo("Resposta do staff purificada (sem <script> nem javascript:)",
      f"ok{marca}" in r.text and sem_xss(r.text) and "javascript:alert" not in r.text)

r = admin.post(f"{BASE}/staff/tickets/view/{tid}", data={
    "csrf_test_name": csrf(r.text), "do": "save_notes", "noteBook": f"Nota {XSS}"})
r = admin.get(f"{BASE}/staff/tickets/view/{tid}")
passo("Notas internas escapadas", "Nota " in r.text and sem_xss(r.text))

# Dados antigos já gravados com HTML perigoso (simula a BD de produção)
sql(f"UPDATE hdz_tickets_messages SET message=CONCAT(message, '{XSS}') WHERE ticket_id={tid}")
r = admin.get(f"{BASE}/staff/tickets/view/{tid}")
passo("Mensagens antigas com HTML perigoso são limpas à saída", sem_xss(r.text))

# CVE-2024-46639 / CVE-2022-31398: campos personalizados
r = admin.get(BASE + "/staff/tools/custom-fields/new")
admin.post(BASE + "/staff/tools/custom-fields/new", data={
    "csrf_test_name": csrf(r.text), "do": "submit", "type": "select", "title": f"Campo {XSS}",
    "options": f"Opção A\nOpção {XSS}", "required": "0", "department_list": "0"})
fid = sql("SELECT MAX(id) FROM hdz_custom_fields")
r = admin.get(f"{BASE}/staff/tools/custom-fields/edit/{fid}")
admin.post(f"{BASE}/staff/tools/custom-fields/edit/{fid}", data={
    "csrf_test_name": csrf(r.text), "do": "submit", "type": "select", "title": f"Editado {XSS}",
    "options": f"Opção A\nOpção {XSS}", "required": "0", "department_list": "0"})
r = admin.get(BASE + "/staff/tools/custom-fields")
passo("Lista de campos personalizados escapada (CVE-2024-46639)", "Editado" in r.text and sem_xss(r.text))
c = requests.Session()
r = c.get(BASE + "/submit-ticket")
r = c.post(BASE + "/submit-ticket", data={"csrf_test_name": csrf(r.text), "do": "submit", "department": "1"})
passo("Formulário do cliente escapa campos personalizados", "Editado" in r.text and sem_xss(r.text))
sql(f"DELETE FROM hdz_custom_fields WHERE id={fid}")

# CVE-2022-31400: nome do endereço de email
sql(f"UPDATE hdz_emails SET name='Suporte {XSS}' WHERE id=1")
r = admin.get(BASE + "/staff/setup/email-addresses")
passo("Lista de endereços de email escapada (CVE-2022-31400)", "Suporte" in r.text and sem_xss(r.text))
sql("UPDATE hdz_emails SET name='Suporte' WHERE id=1")

# ------------------------------------------------------------------ Autorização
print("Autorização")
agente_user = f"agente{marca}"
r = admin.get(BASE + "/staff/agents/new")
admin.post(BASE + "/staff/agents/new", data={
    "csrf_test_name": csrf(r.text), "do": "submit", "fullname": "Agente Teste", "username": agente_user,
    "email": f"{agente_user}@example.test", "password": "agente123", "admin": "0", "active": "1",
    "department[]": ["2"]})
agente = login_staff(agente_user, "agente123")
passo("Agente (só departamento 2) faz login", "/staff/login" not in agente.get(BASE + "/staff/tickets").url)

alvo = criar_bilhete("Vítima", f"vitima{marca}@example.test", f"Alvo {marca}", departamento="1")
r = agente.get(f"{BASE}/staff/tickets/view/{alvo}")
passo("Agente não abre bilhete de outro departamento", f"Alvo {marca}" not in r.text)
r = agente.get(BASE + "/staff/tickets")
agente.post(BASE + "/staff/tickets", data={"csrf_test_name": csrf(r.text), "action": "remove", "ticket_id[]": [alvo]})
agente.post(BASE + "/staff/tickets", data={"csrf_test_name": csrf(agente.get(BASE + "/staff/tickets").text),
                                           "action": "update", "status": "3", "ticket_id[]": [alvo]})
existe = sql(f"SELECT COUNT(*), MAX(status) FROM hdz_tickets WHERE id={alvo}").split()
passo("Ação em massa não apaga bilhete de outro departamento", existe[0] == "1")
passo("Ação em massa não altera bilhete de outro departamento", existe[1] != "3", f"status={existe[1]}")

# Agente sem departamentos (erro mais frequente nos logs de produção: 500 em /staff/tickets)
sem_dep = f"semdep{marca}"
r = admin.get(BASE + "/staff/agents/new")
admin.post(BASE + "/staff/agents/new", data={
    "csrf_test_name": csrf(r.text), "do": "submit", "fullname": "Sem Departamentos", "username": sem_dep,
    "email": f"{sem_dep}@example.test", "password": "agente123", "admin": "0", "active": "1"})
agente0 = login_staff(sem_dep, "agente123")
r = agente0.get(BASE + "/staff/tickets")
passo("Agente sem departamentos abre a lista sem erro 500", r.status_code == 200, f"HTTP {r.status_code}")
passo("Agente sem departamentos não vê bilhetes", "/staff/tickets/view/" not in r.text)
r = agente0.get(f"{BASE}/staff/tickets/view/{alvo}")
passo("Agente sem departamentos não abre bilhetes", r.status_code == 200 and f"Alvo {marca}" not in r.text,
      f"HTTP {r.status_code}")

# ------------------------------------------------------------------ CSRF em eliminação de anexos
print("CSRF")
png = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
       b"\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")
tanexo = criar_bilhete("Anexo", f"anexo{marca}@example.test", f"Anexo {marca}", ficheiro=("pixel.png", png, "image/png"))
fid = sql(f"SELECT id FROM hdz_attachments WHERE ticket_id={tanexo} LIMIT 1")
passo("Anexo gravado", fid != "")
admin.get(f"{BASE}/staff/tickets/view/{tanexo}?delete_file={fid}")
passo("Link GET ?delete_file já não apaga", sql(f"SELECT COUNT(*) FROM hdz_attachments WHERE id={fid}") == "1")
r = admin.get(f"{BASE}/staff/tickets/view/{tanexo}")
admin.post(f"{BASE}/staff/tickets/view/{tanexo}", data={"csrf_test_name": csrf(r.text), "do": "delete_file", "file_id": fid})
passo("Eliminação por POST (com CSRF) funciona", sql(f"SELECT COUNT(*) FROM hdz_attachments WHERE id={fid}") == "0")
r = admin.post(f"{BASE}/staff/tickets/view/{tanexo}", data={"do": "delete_file", "file_id": fid}, allow_redirects=False)
passo("POST sem token CSRF é rejeitado", r.status_code in (302, 303, 403))

# ------------------------------------------------------------------ Recuperação de password
print("Recuperação de password")
email = f"vitima{marca}@example.test"
uid, hash_antes = sql(f"SELECT id, password FROM hdz_users WHERE email='{email}'").split("\t")
c = requests.Session()
r = c.get(BASE + "/forgot-password")
r = c.post(BASE + "/forgot-password", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": "naoexiste@example.test"})
msg_inexistente = BeautifulSoup(r.text, "html.parser").select_one(".alert")
r = c.post(BASE + "/forgot-password", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": email})
msg_existente = BeautifulSoup(r.text, "html.parser").select_one(".alert")
passo("Mesma resposta para email existente e inexistente",
      msg_inexistente and msg_existente and msg_inexistente.get_text() == msg_existente.get_text())
passo("Pedir recuperação NÃO altera a password", sql(f"SELECT password FROM hdz_users WHERE id={uid}") == hash_antes)

segredo = re.search(r"'([0-9a-f]{64})'", (ROOT / "hdz/writable/hdz_secret.php").read_text()).group(1)
expira = int(time.time()) + 3600
assin = hmac.new(segredo.encode(), f"{uid}|{expira}|{hash_antes}".encode(), hashlib.sha256).hexdigest()
link = f"{BASE}/reset-password/{uid}/{expira}/{assin}"
r = c.get(f"{BASE}/reset-password/{uid}/{expira}/{'0' * 64}")
passo("Link com assinatura falsa é recusado", 'name="new_password"' not in r.text)
expirado = int(time.time()) - 10
assin_exp = hmac.new(segredo.encode(), f"{uid}|{expirado}|{hash_antes}".encode(), hashlib.sha256).hexdigest()
r = c.get(f"{BASE}/reset-password/{uid}/{expirado}/{assin_exp}")
passo("Link expirado é recusado", 'name="new_password"' not in r.text)
r = c.get(link)
passo("Link válido mostra o formulário", 'name="new_password"' in r.text)
r = c.post(link, data={"csrf_test_name": csrf(r.text), "do": "submit", "new_password": "NovaPass123", "new_password2": "NovaPass123"})
passo("Nova password definida", sql(f"SELECT password FROM hdz_users WHERE id={uid}") != hash_antes)
r = c.get(link)
passo("Link não pode ser reutilizado", 'name="new_password"' not in r.text)
c2 = requests.Session()
r = c2.get(BASE + "/login")
r = c2.post(BASE + "/login", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": email, "password": "NovaPass123"})
passo("Login com a nova password", "/tickets" in r.url, r.url)

# ------------------------------------------------------------------ Tokens
print("Tokens")
token = sql(f"SELECT token FROM hdz_users WHERE id={uid}")
passo("Token de sessão do cliente com 60 caracteres alfanuméricos", re.fullmatch(r"[0-9A-Za-z]{60}", token or "") is not None, token)

# ------------------------------------------------------------------ Pipe (path traversal)
print("Email por pipe")
alvo_ficheiro = ROOT / "upload" / f"pwn{marca}.php"
email_suporte = sql("SELECT email FROM hdz_emails ORDER BY `default` DESC LIMIT 1")
eml = f"""From: Atacante <atacante{marca}@example.test>
To: {email_suporte}
Subject: Pipe {marca}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="XX"

--XX
Content-Type: text/plain; charset=utf-8

Corpo
--XX
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="../../../upload/pwn{marca}.php"

<?php echo 'pwned'; ?>
--XX--
"""
r = subprocess.run(PHP + ["pipe.php"], input=eml, capture_output=True, text=True, cwd=ROOT)
tpipe = sql(f"SELECT id FROM hdz_tickets WHERE subject='Pipe {marca}'")
passo("Email por pipe cria bilhete", tpipe != "", r.stdout[-300:] + r.stderr[-300:])
passo("Anexo com '../' não escreve fora da pasta de anexos", not alvo_ficheiro.exists())
nome = sql(f"SELECT name FROM hdz_attachments WHERE ticket_id={tpipe or 0}")
passo("Nome do anexo guardado sem caminho", nome == f"pwn{marca}.php", nome)
r = requests.get(BASE + "/mail_pipe")
passo("Rota /mail_pipe não acessível pela web", r.status_code == 404, f"HTTP {r.status_code}")

# ------------------------------------------------------------------ Limite de tentativas (no fim: bloqueia o IP 5 min)
print("Limite de tentativas no login de clientes")
c3 = requests.Session()
for i in range(3):
    r = c3.get(BASE + "/login")
    c3.post(BASE + "/login", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": email, "password": "errada"})
r = c3.get(BASE + "/login")
r = c3.post(BASE + "/login", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": email, "password": "NovaPass123"})
passo("Após 3 falhas, o login fica bloqueado (mesmo com a password certa)", "/tickets" not in r.url)
sql("DELETE FROM hdz_login_attempt WHERE ip LIKE 'client:%'")

print()
print("RESULTADO:", "tudo OK" if falhas == 0 else f"{falhas} falha(s)")
sys.exit(1 if falhas else 0)
