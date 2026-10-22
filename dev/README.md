# Ambiente de desenvolvimento — HelpDeskZ AESCAS

Fork de manutenção do [HelpDeskZ 2.0.2](https://github.com/helpdesk-z/helpdeskz-dev), usado em `suporte.aescas.net`.

> **A produção nunca é alterada a partir daqui.** Todo o desenvolvimento e teste é feito localmente.

## Opção A — Docker (recomendado)

Espelha a produção: PHP 8.4 + Apache 2.4 + MySQL 8.0, mais o Mailpit para apanhar os emails.

```bash
cp dev/Helpdesk.dev.php hdz/app/Config/Helpdesk.php
docker compose up -d --build
```

1. Abre <http://localhost:8080/install> e segue o assistente (cria a conta de administrador).
2. Painel de staff: <http://localhost:8080/staff>
3. Emails enviados pela app: <http://localhost:8025>
   Em *Setup → Email Addresses → Saída*, escolhe SMTP com host `mailpit`, porta `1025`, sem encriptação.

Para recomeçar do zero: `docker compose down -v` (apaga a base de dados) e
`rm hdz/writable/cache/install.config` (desbloqueia o instalador).

## Opção B — Sem Docker (PHP + MySQL locais)

```bash
# Base de dados
mysql -u root -e "CREATE DATABASE helpdeskz CHARACTER SET utf8mb4;
  CREATE USER 'hdz'@'localhost' IDENTIFIED BY 'hdzdev';
  GRANT ALL ON helpdeskz.* TO 'hdz'@'localhost';"

cp dev/Helpdesk.dev.php hdz/app/Config/Helpdesk.php
php -S localhost:8080 dev/router.php
```

Extensões PHP necessárias: `intl`, `mbstring`, `mysqli`, `fileinfo`, `iconv`, `imap`.

## Teste de fumo

Percorre os fluxos principais (portal do cliente, criação de bilhete, painel de staff, proteções):

```bash
pip install requests beautifulsoup4
python3 dev/smoke_test.py http://localhost:8080 admin <password>
```

Corre-o antes e depois de cada alteração. **Nunca o corras contra a produção** — cria bilhetes e utilizadores.

## Fluxo de trabalho

- `master` = código que pode ir para produção.
- Cada correção ou funcionalidade num ramo próprio (`fase1-seguranca`, …) com pull request.
- Antes de publicar em produção: cópia de segurança dos ficheiros e da base de dados.
