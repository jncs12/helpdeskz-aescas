<?php
/**
 * Tarefas que só correm depois de a resposta já ter sido entregue ao navegador.
 *
 * Usado para os emails de notificação: antes, abrir um ticket esperava pelo envio de um email
 * ao utilizador e de outro a cada colaborador da área (cada um com a sua ligação SMTP ao Gmail).
 * Com vários colaboradores, isso levava dezenas de segundos — e quem voltava a carregar em
 * «Enviar» criava tickets duplicados.
 *
 * Com PHP-FPM (fastcgi_finish_request) ou LiteSpeed/mod_lsapi (litespeed_finish_request) o
 * pedido é fechado antes de as tarefas correrem. Com mod_php envia-se a resposta com o tamanho
 * exato (Content-Length), o que basta ao navegador e ao nginx para a darem por concluída.
 * Na linha de comandos (pipe de email, cron) as tarefas correm logo, tal como antes.
 */

namespace App\Libraries;

use CodeIgniter\Events\Events;

class AfterResponse
{
    /** @var callable[] */
    protected static $tasks = [];
    protected static $registered = false;

    /**
     * Agenda uma tarefa para depois da resposta (ou corre-a já, se não for possível).
     */
    public static function run(callable $task): void
    {
        if (!static::canDetach()) {
            static::execute($task);
            return;
        }
        static::$tasks[] = $task;
        if (!static::$registered) {
            static::$registered = true;
            // 'post_system' é disparado pelo CodeIgniter logo depois de enviar a resposta
            Events::on('post_system', [static::class, 'flush']);
        }
    }

    /**
     * Só vale a pena adiar num pedido web cujo servidor permita terminar a resposta mais cedo.
     */
    public static function canDetach(): bool
    {
        if (is_cli() || (defined('ENVIRONMENT') && ENVIRONMENT === 'testing')) {
            return false;
        }
        return static::hasFinishRequest() || PHP_SAPI === 'apache2handler';
    }

    protected static function hasFinishRequest(): bool
    {
        return function_exists('fastcgi_finish_request') || function_exists('litespeed_finish_request');
    }

    /**
     * Termina a resposta ao navegador e corre as tarefas pendentes.
     */
    public static function flush(): void
    {
        if (empty(static::$tasks)) {
            return;
        }
        // Grava e liberta a sessão: o pedido seguinte do mesmo utilizador (o redirecionamento
        // para a página do ticket) ficaria bloqueado à espera dela até as tarefas acabarem.
        if (session_status() === PHP_SESSION_ACTIVE) {
            session_write_close();
        }
        // Se o utilizador fechar a página, as tarefas continuam
        ignore_user_abort(true);
        @set_time_limit(300);

        if (static::hasFinishRequest()) {
            while (ob_get_level() > 0) {
                ob_end_flush();
            }
            if (function_exists('fastcgi_finish_request')) {
                fastcgi_finish_request();
            } else {
                litespeed_finish_request();
            }
        } elseif (!headers_sent()) {
            // mod_php (Apache): não há forma de fechar o pedido, mas indicar o tamanho exato
            // da resposta deixa o navegador (e o nginx à frente) dá-la por concluída logo.
            while (ob_get_level() > 1) {
                ob_end_flush();
            }
            $body = ob_get_level() > 0 ? (string) ob_get_clean() : '';
            header('Content-Length: ' . strlen($body));
            header('Connection: close');
            echo $body;
            flush();
        } else {
            while (ob_get_level() > 0) {
                ob_end_flush();
            }
        }

        $tasks = static::$tasks;
        static::$tasks = [];
        foreach ($tasks as $task) {
            static::execute($task);
        }
    }

    protected static function execute(callable $task): void
    {
        try {
            $task();
        } catch (\Throwable $e) {
            // Uma falha num email não pode impedir os seguintes nem mostrar erro ao utilizador
            log_message('error', 'AfterResponse: ' . $e->getMessage() . ' em ' . $e->getFile() . ':' . $e->getLine());
        }
    }
}
