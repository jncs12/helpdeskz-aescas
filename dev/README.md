# Ambiente de desenvolvimento — HelpDeskZ AESCAS

Fork de manutenção do [HelpDeskZ 2.0.2](https://github.com/helpdesk-z/helpdeskz-dev), usado em `suporte.aescas.net`.

> **A produção nunca é alterada a partir daqui.** Todo o desenvolvimento e teste é feito localmente.

## Opção A — Docker (recomendado; macOS, Windows ou Linux)

Espelha a produção: PHP 8.4 + Apache 2.4 + MySQL 8.0, mais o Mailpit para apanhar os emails.

### 1. Instalar (uma vez)

- **Docker Desktop**: <https://www.docker.com/products/docker-desktop/> (no Mac, escolhe a versão
  Apple Silicon ou Intel conforme o teu processador). Abre-o uma vez e espera que diga «Engine running».
- **Git**: no Mac já vem com as *Command Line Tools* (`xcode-select --install` se faltar).

### 2. Descarregar o código

```bash
git clone https://github.com/jncs12/helpdeskz-aescas.git
cd helpdeskz-aescas
cp dev/Helpdesk.dev.php hdz/app/Config/Helpdesk.php
```

### 3a. Instalação limpa (para experimentar)

```bash
docker compose up -d --build      # a primeira vez demora alguns minutos
```

1. Abre <http://localhost:8080/install> e segue o assistente (cria a conta de administrador).
2. Painel de staff: <http://localhost:8080/staff>
3. Emails enviados pela app: <http://localhost:8025>
   Em *Configurações → Endereços de e-mail → Saída*, escolhe SMTP com servidor `mailpit`, porta `1025`, sem encriptação.

### 3b. Com uma cópia da BD de produção (os teus dados reais)

1. No phpMyAdmin da produção, exporta a base de dados (formato SQL) para, por exemplo, `producao.sql`.
   Usa a exportação «Rápida»; se escolheres «Personalizada», não marques «CREATE DATABASE / USE».
2. Cria um ficheiro `.env` na pasta do projeto com o prefixo das tabelas da produção:
   ```bash
   echo "HDZ_DB_PREFIX=hdzin_" > .env
   ```
3. Arranca e importa:
   ```bash
   docker compose up -d --build
   docker compose exec -T db mysql -uhdz -phdzdev helpdeskz < producao.sql
   docker compose exec -T db mysql -uhdz -phdzdev helpdeskz < dev/sql/preparar_copia_local.sql
   touch hdz/writable/cache/install.config     # bloqueia o instalador
   ```
4. Entra em <http://localhost:8080/staff> com as tuas credenciais de produção.

O `preparar_copia_local.sql` envia **todos os emails para o Mailpit** (nenhum chega a alunos ou colegas)
e desliga o reCAPTCHA. Os anexos não vêm na exportação da BD: os links de download dão «ficheiro não
encontrado», a não ser que copies também `hdz/writable/attachments/`.

> A cópia tem dados pessoais. Apaga o `producao.sql` quando acabares e não o juntes ao Git
> (o `.gitignore` já ignora ficheiros `producao*.sql`).

### Parar e recomeçar

```bash
docker compose stop          # para (os dados ficam)
docker compose start         # volta a arrancar
docker compose down -v       # apaga tudo, incluindo a base de dados
```

Para voltar a correr o instalador: `rm hdz/writable/cache/install.config`.

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

## Testes de segurança

Tentam explorar cada falha corrigida (XSS, CVE conhecidas, autorização, CSRF, recuperação de password,
path traversal no pipe, limite de tentativas). Precisam de acesso à BD e de correr na mesma máquina da app:

```bash
python3 dev/security_test.py http://localhost:8080 admin <password>

# Com Docker:
HDZ_MYSQL="docker compose exec -T db mysql -uhdz -phdzdev helpdeskz" \
HDZ_PHP="docker compose exec -T app php" \
python3 dev/security_test.py http://localhost:8080 admin <password>
```

No fim bloqueiam o login de clientes do teu IP durante uns minutos (é o próprio teste do bloqueio) —
o script limpa esse bloqueio, mas convém saberes.

## Fluxo de trabalho

- `master` = código que pode ir para produção.
- Cada correção ou funcionalidade num ramo próprio (`fase1-seguranca`, …) com pull request.
- Antes de publicar em produção: cópia de segurança dos ficheiros e da base de dados.
