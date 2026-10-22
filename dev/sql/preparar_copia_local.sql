-- ---------------------------------------------------------------------------
-- Prepara uma CÓPIA da BD de produção para correr no ambiente local (Docker).
-- NUNCA correr na produção.
--
-- Todos os emails passam a ir para o Mailpit (http://localhost:8025): nenhum
-- email sai para alunos ou colegas, mas consegues ver o que seria enviado.
-- A entrada por IMAP/pipe fica desligada.
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;

UPDATE `hdzin_emails` SET
  `outgoing_type`   = 'smtp',
  `smtp_host`       = 'mailpit',
  `smtp_port`       = '1025',
  `smtp_encryption` = '',
  `smtp_username`   = '',
  `smtp_password`   = '',
  `incoming_type`   = '',
  `imap_password`   = '';

-- Desliga o reCAPTCHA (as chaves de produção não funcionam em localhost)
UPDATE `hdzin_config` SET `recaptcha` = 0;
