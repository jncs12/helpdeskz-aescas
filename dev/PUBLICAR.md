# Publicação em produção (Fase 1: segurança + tradução pt-PT)

Checklist para levar as correções de segurança para `suporte.aescas.net`.

## O que se sabe da produção (análise de 2026-10-22)

- O código em produção é **exatamente o HelpDeskZ 2.0.2** (março de 2021), sem alterações ao código.
  Faltam-lhe também as correções publicadas depois no GitHub, que este repositório já inclui
  (por exemplo: em *Setup → Email Addresses* qualquer ação dá «This is not possible in demo version»).
- As únicas personalizações são: a tradução (escrita **por cima** de `Language/en`), o `.htaccess`,
  o `favicon.ico`, o logótipo em `upload/` e o `hdz/app/Config/Helpdesk.php`.
- A tradução passa a viver em `Language/pt-PT`, revista para português europeu com tratamento por «tu».
  `Language/en` volta a ser o inglês original.
- Prefixo das tabelas na BD de produção: `hdzin_` (não `hdz_`). Ter isto em conta ao testar com uma cópia.

## Antes

1. **Cópia de segurança** completa: ficheiros do site e base de dados (cPanel → Backup, ou `mysqldump`).
2. Testar localmente com uma cópia da BD de produção:
   `python3 dev/smoke_test.py` e `python3 dev/security_test.py` têm de dar «tudo OK».

## Publicar

Copiar os ficheiros alterados (lista: `git diff --name-only 0561d07..fase1-traducao-pt`),
exceto a pasta `dev/`, o `docker-compose.yml`, o `.gitignore` e o `hdz/app/Config/Helpdesk.php`.

Ficheiros novos que têm de ir: `hdz/.htaccess`, `hdz/app/Views/client/reset_password.php`,
a pasta `hdz/app/Language/pt-PT/`.

**Ao mesmo tempo** (senão a interface fica em inglês):
- substituir `hdz/app/Language/en/` pelo inglês original deste repositório;
- no `hdz/app/Config/Helpdesk.php` da produção, mudar só esta linha:
  `const DEFAULT_LANG = 'pt-PT';`

Podem ser apagados da produção depois de confirmares que está tudo bem (já não são usados):
`hdz/app/Language/en/backup/`, `hdz/app/Language/en/backup.2/`, `hdz/app/Language/en.en/`.

## Depois

1. **Modelos de email** (Setup → Email Templates). O email de recuperação deixou de levar uma password
   nova e passa a levar um link válido durante 1 hora. Os modelos antigos continuam a funcionar
   (o `%client_password%` passa a conter o link), mas o texto fica errado.
   Recomendado: correr `dev/sql/modelos_email_pt-PT.sql` no phpMyAdmin, que põe os 6 modelos em
   português europeu (tratamento por «tu») sem mexer no estado ativo/inativo de cada um.
   **Exporta antes a tabela `hdzin_emails_tpl`**, porque o script substitui os textos atuais.

2. Confirmar que `hdz/writable/` continua com permissão de escrita: é aí que é criado automaticamente o
   `hdz_secret.php` (chave que assina os links de redefinição). Não o apagar nem partilhar.
3. Testes manuais rápidos: login de staff, abrir e responder a um bilhete, criar um bilhete como cliente,
   pedir «Esqueceste-te da palavra-passe?» com uma conta de teste.

## Mudanças de comportamento que os utilizadores podem notar

- «Esqueci-me da password» envia um **link** (antes enviava uma password nova).
- O login de clientes passa a ser bloqueado após várias tentativas falhadas (mesma configuração do staff:
  *Setup → Security → tentativas / minutos*).
- Novas passwords escolhidas pelo link têm de ter pelo menos 8 caracteres.
- O botão «Apagar» dos anexos pede confirmação.
- Agentes só conseguem aplicar ações em massa a bilhetes dos seus departamentos.

## Reverter

Repor a cópia de segurança dos ficheiros. Esta fase não altera a estrutura da base de dados.
