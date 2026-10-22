# Publicação da Fase 1 (segurança) em produção

Checklist para levar as correções de segurança para `suporte.aescas.net`.

## Antes

1. **Cópia de segurança** completa: ficheiros do site e base de dados (cPanel → Backup, ou `mysqldump`).
2. **Comparar a produção com o código original 2.0.2.** A produção tem a interface em português e pode ter
   outras alterações locais que não estão neste repositório. Copiar os ficheiros por cima sem comparar
   pode apagá-las. O ideal é trazer primeiro uma cópia de `hdz/app` da produção para o repositório.
3. Testar localmente com uma cópia da BD de produção:
   `python3 dev/smoke_test.py` e `python3 dev/security_test.py` têm de dar «tudo OK».

## Publicar

Copiar os ficheiros alterados neste ramo (lista: `git diff --name-only master...fase1-seguranca`),
exceto a pasta `dev/`, o `docker-compose.yml` e o `hdz/app/Config/Helpdesk.php` (esse é o da produção — não mexer).

Ficheiros novos que têm de ir: `hdz/.htaccess`, `hdz/app/Views/client/reset_password.php`.

## Depois

1. **Modelo de email «Lost password confirmation»** (Setup → Email Templates).
   O email deixou de levar uma password nova e passa a levar um link de redefinição válido 1 hora.
   Os modelos antigos continuam a funcionar (o `%client_password%` passa a conter o link), mas o texto
   fica estranho. Texto sugerido:

   > Recebemos um pedido para redefinir a password da tua conta no %company_name%.
   > Para escolheres uma nova password, abre este link (válido durante 1 hora):
   > %reset_link%
   > Se não fizeste este pedido, ignora este email — a tua password não foi alterada.

2. **Traduções**: as novas mensagens foram acrescentadas a `Language/en/Client.php`
   (`resetLinkSent`, `resetTitle`, `resetDescription`, `resetInvalidTitle`, `resetInvalid`,
   `passwordChanged`, `tooManyAttempts`, `enterPassword`, `passwordTooShort`). Têm de ser acrescentadas
   também ao ficheiro de português usado em produção.
3. Confirmar que `hdz/writable/` continua com permissão de escrita: é aí que é criado automaticamente o
   `hdz_secret.php` (chave que assina os links de redefinição). Não o apagar nem partilhar.
4. Testes manuais rápidos: login de staff, abrir e responder a um bilhete, criar um bilhete como cliente,
   pedir «Esqueci-me da password» com uma conta de teste.

## Mudanças de comportamento que os utilizadores podem notar

- «Esqueci-me da password» envia um **link** (antes enviava uma password nova).
- O login de clientes passa a ser bloqueado após várias tentativas falhadas (mesma configuração do staff:
  *Setup → Security → tentativas / minutos*).
- Novas passwords escolhidas pelo link têm de ter pelo menos 8 caracteres.
- O botão «Apagar» dos anexos pede confirmação.
- Agentes só conseguem aplicar ações em massa a bilhetes dos seus departamentos.

## Reverter

Repor a cópia de segurança dos ficheiros. Esta fase não altera a estrutura da base de dados.
