<?php
/**
 * Router para o servidor embutido do PHP (alternativa ao Docker):
 *   cp dev/Helpdesk.dev.php hdz/app/Config/Helpdesk.php
 *   php -S localhost:8080 dev/router.php
 * Serve ficheiros estáticos existentes; o resto vai para index.php
 * (equivalente às regras de rewrite do .htaccess).
 */
$root = dirname(__DIR__);
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$file = realpath($root . $path);

// Nunca servir diretamente ficheiros internos (equivale aos .htaccess "deny")
if ($file !== false && str_starts_with($file, $root . DIRECTORY_SEPARATOR . 'hdz')) {
    http_response_code(403);
    exit('Forbidden');
}
if ($path !== '/' && $file !== false && is_file($file) && str_starts_with($file, $root)) {
    return false;
}
$_SERVER['SCRIPT_NAME'] = '/index.php';
$_SERVER['SCRIPT_FILENAME'] = $root . '/index.php';
chdir($root);
require $root . '/index.php';
