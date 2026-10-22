-- ---------------------------------------------------------------------------
-- Modelos de email do HelpDeskZ em português europeu, tratamento por «tu».
--
-- Atualiza só o nome, o assunto e o texto de cada modelo. O estado
-- (ativo/inativo) que tens em Setup → Email Templates NÃO é alterado.
--
-- ANTES DE CORRER:
--   1. Exporta a tabela atual (phpMyAdmin → tabela → Exportar), porque este
--      script substitui os textos que lá estiverem.
--   2. Confirma o prefixo das tabelas: em produção é «hdzin_». No ambiente
--      de desenvolvimento é «hdz_»:  sed 's/`hdzin_/`hdz_/g' este_ficheiro.sql
--
-- Marcadores disponíveis (substituídos automaticamente no envio):
--   %company_name% %support_url% %client_name% %client_email%
--   %client_password% %reset_link% %staff_name% %message%
--   %ticket_id% %ticket_subject% %ticket_department% %ticket_status%
--   %ticket_priority%
-- ---------------------------------------------------------------------------

SET NAMES utf8mb4;

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Boas-vindas (novo registo)',
  `subject` = 'Bem-vindo ao helpdesk %company_name%',
  `message` = '<p>Olá %client_name%,</p>\r\n<p>A tua conta no helpdesk %company_name% foi criada.</p>\r\n<p><strong>E-mail:</strong> %client_email%<br /><strong>Palavra-passe:</strong> %client_password%</p>\r\n<p>Recomendamos que alteres a palavra-passe depois de entrares pela primeira vez (Conta → Alterar palavra-passe).</p>\r\n<p>No helpdesk podes consultar a Base de Conhecimento, abrir pedidos de suporte e acompanhar o estado dos teus tickets:<br />%support_url%</p>\r\n<p>Até breve,<br />%company_name%</p>'
WHERE `id` = 'new_user';

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Recuperação de palavra-passe',
  `subject` = 'Redefinir a palavra-passe no helpdesk %company_name%',
  `message` = '<p>Olá %client_name%,</p>\r\n<p>Recebemos um pedido para redefinir a palavra-passe da tua conta no helpdesk %company_name%.</p>\r\n<p>Para escolheres uma nova palavra-passe, abre este link (válido durante 1 hora):<br /><a href="%reset_link%">%reset_link%</a></p>\r\n<p>Se não fizeste este pedido, ignora este e-mail. A tua palavra-passe não foi alterada.</p>\r\n<p>%company_name%<br />Helpdesk: %support_url%</p>'
WHERE `id` = 'lost_password';

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Novo ticket (confirmação ao utilizador)',
  `subject` = '[#%ticket_id%] %ticket_subject%',
  `message` = '<p>Olá %client_name%,</p>\r\n<p>Obrigado pelo teu contacto. Esta é uma resposta automática para confirmar que recebemos o teu pedido. Vamos responder-te o mais depressa possível.</p>\r\n<p>Se responderes a este e-mail, mantém o número do ticket no assunto, para que a tua resposta fique associada ao pedido certo.</p>\r\n<p><strong>Ticket:</strong> #%ticket_id%<br /><strong>Assunto:</strong> %ticket_subject%<br /><strong>Área:</strong> %ticket_department%<br /><strong>Estado:</strong> %ticket_status%<br /><strong>Prioridade:</strong> %ticket_priority%</p>\r\n<p>Podes acompanhar ou responder ao ticket em: %support_url%</p>\r\n<p>%company_name%</p>'
WHERE `id` = 'new_ticket';

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Resposta automática a nova mensagem',
  `subject` = '[#%ticket_id%] %ticket_subject%',
  `message` = '<p>Olá %client_name%,</p>\r\n<p>Recebemos a tua resposta ao ticket #%ticket_id%.</p>\r\n<p><strong>Ticket:</strong> #%ticket_id%<br /><strong>Área:</strong> %ticket_department%<br /><strong>Estado:</strong> %ticket_status%<br /><strong>Prioridade:</strong> %ticket_priority%<br /><strong>Helpdesk:</strong> %support_url%</p>'
WHERE `id` = 'autoresponse';

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Resposta da equipa',
  `subject` = 'Re: [#%ticket_id%] %ticket_subject%',
  `message` = '<p>%message%</p>\r\n<hr />\r\n<p><strong>Ticket:</strong> #%ticket_id%<br /><strong>Área:</strong> %ticket_department%<br /><strong>Estado:</strong> %ticket_status%<br /><strong>Prioridade:</strong> %ticket_priority%<br /><strong>Helpdesk:</strong> %support_url%</p>'
WHERE `id` = 'staff_reply';

UPDATE `hdzin_emails_tpl` SET
  `name` = 'Novo ticket (aviso à equipa)',
  `subject` = '[#%ticket_id%] Novo ticket: %ticket_subject%',
  `message` = '<p>Olá %staff_name%,</p>\r\n<p>Foi aberto um novo ticket numa das tuas áreas. Entra no painel de staff para lhe responderes.</p>\r\n<p><strong>Ticket:</strong> #%ticket_id%<br /><strong>Assunto:</strong> %ticket_subject%<br /><strong>Área:</strong> %ticket_department%<br /><strong>Estado:</strong> %ticket_status%<br /><strong>Prioridade:</strong> %ticket_priority%<br /><strong>Helpdesk:</strong> %support_url%</p>'
WHERE `id` = 'staff_ticketnotification';
