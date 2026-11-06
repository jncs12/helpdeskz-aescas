#!/usr/bin/env python3
"""
Testes da proteção contra tickets e respostas duplicadas.

Simula o que acontece quando alguém carrega várias vezes em «Enviar»: o mesmo formulário
chega ao servidor várias vezes, quase ao mesmo tempo ou com uns segundos de intervalo.
Em cada caso só pode ficar gravado UM ticket / UMA resposta.

Uso:
    pip install requests beautifulsoup4
    python3 dev/duplicados_test.py [URL_BASE] [ADMIN] [PASSWORD]

Variáveis de ambiente (iguais às do security_test.py):
    HDZ_MYSQL  comando para a BD   (omissão: "mysql -uhdz -phdzdev -h127.0.0.1 helpdeskz")
               com Docker:         "docker compose exec -T db mysql -uhdz -phdzdev helpdeskz"
    HDZ_PHP    comando PHP da app  (omissão: "php"; com Docker: "docker compose exec -T app php")
    HDZ_PREFIX prefixo das tabelas (omissão: "hdz_")

NUNCA correr contra a produção: cria bilhetes e utilizadores.
"""
import os
import re
import shlex
import subprocess
import sys
import threading
import time

import requests
from bs4 import BeautifulSoup

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080").rstrip("/")
ADMIN = sys.argv[2] if len(sys.argv) > 2 else "admin"
ADMIN_PASS = sys.argv[3] if len(sys.argv) > 3 else "admin123"
MYSQL = shlex.split(os.environ.get("HDZ_MYSQL", "mysql -uhdz -phdzdev -h127.0.0.1 helpdeskz"))
PHP = shlex.split(os.environ.get("HDZ_PHP", "php"))
P = os.environ.get("HDZ_PREFIX", "hdz_")
SEM_ANEXO = {"attachment[]": ("", b"", "application/octet-stream")}

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


def em_paralelo(funcoes):
    """Corre as funções ao mesmo tempo (como vários cliques seguidos) e devolve os resultados."""
    resultados = [None] * len(funcoes)

    def correr(i, f):
        try:
            resultados[i] = f()
        except Exception as e:  # noqa: BLE001
            resultados[i] = e

    fios = [threading.Thread(target=correr, args=(i, f)) for i, f in enumerate(funcoes)]
    for t in fios:
        t.start()
    for t in fios:
        t.join()
    return resultados


def formulario_ticket(sessao):
    """Abre o formulário de novo ticket na área 1 e devolve (url, token CSRF)."""
    r = sessao.get(BASE + "/submit-ticket")
    r = sessao.post(BASE + "/submit-ticket", data={"csrf_test_name": csrf(r.text), "do": "submit", "department": "1"})
    return r.url, csrf(r.text)


def enviar_ticket(sessao, url, token, email, assunto, mensagem):
    return sessao.post(url, data={"csrf_test_name": token, "do": "submit", "fullname": "Teste Duplicados",
                                  "email": email, "subject": assunto, "message": mensagem},
                       files=SEM_ANEXO, timeout=120)


def contar_tickets(assunto):
    return int(sql(f"SELECT COUNT(*) FROM {P}tickets WHERE subject='{assunto}'"))


def contar_mensagens(ticket_id, texto):
    return int(sql(f"SELECT COUNT(*) FROM {P}tickets_messages WHERE ticket_id={int(ticket_id)} AND message LIKE '%{texto}%'"))


# ------------------------------------------------------------------ Cliente: novo ticket
print("Novo ticket (portal do cliente)")

# 1. Três cliques seguidos: o mesmo formulário (mesma sessão e token) enviado 3× em paralelo
c = requests.Session()
url, token = formulario_ticket(c)
email = f"dup{marca}@example.test"
assunto = f"Duplicado paralelo {marca}"
respostas = em_paralelo([lambda: enviar_ticket(c, url, token, email, assunto, "Mensagem igual")] * 3)
erros = [r for r in respostas if isinstance(r, Exception) or r.status_code >= 400]
passo("Os três envios respondem sem erro", not erros, str(erros))
passo("Três envios em paralelo → 1 ticket", contar_tickets(assunto) == 1, f"{contar_tickets(assunto)} tickets")
confirmacoes = [re.search(r"/confirmation/(\d+)/", r.url).group(1)
                for r in respostas if not isinstance(r, Exception) and "/confirmation/" in r.url]
passo("Todos os envios mostram a confirmação do mesmo ticket",
      len(confirmacoes) == 3 and len(set(confirmacoes)) == 1, str(confirmacoes))

# 2. Mesmo email em sessões diferentes (ex.: dois separadores) — testa o bloqueio GET_LOCK
assunto = f"Duplicado sessoes {marca}"  # só ASCII: o cliente mysql pode não usar utf8
email2 = f"dup2{marca}@example.test"
sessoes = [requests.Session() for _ in range(3)]
formularios = [formulario_ticket(s) for s in sessoes]
em_paralelo([(lambda s=s, f=f: enviar_ticket(s, f[0], f[1], email2, assunto, "Mensagem igual"))
             for s, f in zip(sessoes, formularios)])
passo("Três sessões em paralelo, mesmo email → 1 ticket", contar_tickets(assunto) == 1,
      f"{contar_tickets(assunto)} tickets")
passo("Só uma conta de utilizador criada para o email",
      sql(f"SELECT COUNT(*) FROM {P}users WHERE email='{email2}'") == "1")

# 3. Impaciência: volta a enviar 3 s depois (página que parecia não responder)
assunto = f"Duplicado impaciente {marca}"
c = requests.Session()
url, token = formulario_ticket(c)
enviar_ticket(c, url, token, email, assunto, "Mensagem igual")
time.sleep(3)
url, token = formulario_ticket(c)
r = enviar_ticket(c, url, token, email, assunto, "Mensagem igual")
passo("Reenvio 3 s depois → continua 1 ticket", contar_tickets(assunto) == 1, f"{contar_tickets(assunto)} tickets")
passo("O reenvio mostra a confirmação do ticket existente", "/confirmation/" in r.url, r.url)

# 4. Sem falsos positivos: mesmo assunto mas mensagem diferente é outro pedido
url, token = formulario_ticket(c)
enviar_ticket(c, url, token, email, assunto, "Outra mensagem diferente")
passo("Mesmo assunto, mensagem diferente → novo ticket", contar_tickets(assunto) == 2,
      f"{contar_tickets(assunto)} tickets")

# ------------------------------------------------------------------ Cliente: resposta
print("Resposta do cliente")
ticket_cliente = sql(f"SELECT t.id FROM {P}tickets t JOIN {P}users u ON u.id=t.user_id "
                     f"WHERE u.email='{email}' ORDER BY t.id LIMIT 1")
hash_pw = subprocess.run(PHP + ["-r", "echo password_hash('Duplicados123', PASSWORD_BCRYPT);"],
                         capture_output=True, text=True).stdout.strip()
sql(f"UPDATE {P}users SET password='{hash_pw}' WHERE email='{email}'")
c = requests.Session()
r = c.get(BASE + "/login")
c.post(BASE + "/login", data={"csrf_test_name": csrf(r.text), "do": "submit", "email": email, "password": "Duplicados123"})
r = c.get(f"{BASE}/tickets/show/{ticket_cliente}")
passo("Cliente vê o ticket", r.status_code == 200 and "replyForm" in r.text)
token = csrf(r.text)
texto = f"Resposta cliente {marca}"
em_paralelo([lambda: c.post(f"{BASE}/tickets/show/{ticket_cliente}",
                            data={"csrf_test_name": token, "do": "reply", "message": texto},
                            files=SEM_ANEXO, timeout=120)] * 3)
passo("Três respostas iguais em paralelo → 1 mensagem", contar_mensagens(ticket_cliente, texto) == 1,
      f"{contar_mensagens(ticket_cliente, texto)} mensagens")

# ------------------------------------------------------------------ Staff
print("Painel de staff")
s = requests.Session()
r = s.get(BASE + "/staff/login")
s.post(BASE + "/staff/login", data={"csrf_test_name": csrf(r.text), "do": "login",
                                    "username": ADMIN, "password": ADMIN_PASS})
r = s.get(f"{BASE}/staff/tickets/view/{ticket_cliente}")
token = csrf(r.text)
texto = f"Resposta staff {marca}"
em_paralelo([lambda: s.post(f"{BASE}/staff/tickets/view/{ticket_cliente}",
                            data={"csrf_test_name": token, "do": "reply", "status": "2", "message": f"<p>{texto}</p>"},
                            files=SEM_ANEXO, timeout=120)] * 3)
passo("Três respostas do staff em paralelo → 1 mensagem", contar_mensagens(ticket_cliente, texto) == 1,
      f"{contar_mensagens(ticket_cliente, texto)} mensagens")

r = s.get(BASE + "/staff/tickets/create")
token = csrf(r.text)
assunto = f"Duplicado staff {marca}"
respostas = em_paralelo([lambda: s.post(BASE + "/staff/tickets/create", data={
    "csrf_test_name": token, "do": "submit", "email": f"dup3{marca}@example.test", "fullname": "Teste",
    "department": "1", "priority": "1", "status": "1", "subject": assunto, "message": "<p>Igual</p>"},
    files=SEM_ANEXO, timeout=120)] * 3)
passo("Três tickets do staff em paralelo → 1 ticket", contar_tickets(assunto) == 1, f"{contar_tickets(assunto)} tickets")
passo("Todos abrem a vista do ticket",
      all(not isinstance(r, Exception) and "/staff/tickets/view/" in r.url for r in respostas),
      str([getattr(r, "url", r) for r in respostas]))

# ------------------------------------------------------------------ Botão no navegador
print("Formulários")
c = requests.Session()
url, _ = formulario_ticket(c)
html = c.get(url).text
passo("Formulário de novo ticket tem data-submit-once", "data-submit-once=" in html)
passo("submit-once.js incluído no portal", "submit-once.js" in html)
passo("submit-once.js acessível", requests.get(BASE + "/assets/helpdeskz/js/submit-once.js").status_code == 200)
html = s.get(BASE + "/staff/tickets/create").text
passo("Novo ticket (staff) tem data-submit-once", "data-submit-once=" in html and "submit-once.js" in html)

print()
print("RESULTADO: " + ("tudo OK" if falhas == 0 else f"{falhas} falha(s)"))
sys.exit(1 if falhas else 0)
