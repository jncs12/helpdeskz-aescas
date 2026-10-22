<?php
/**
 * Configuração para o ambiente de DESENVOLVIMENTO.
 * Copiar para hdz/app/Config/Helpdesk.php:
 *   cp dev/Helpdesk.dev.php hdz/app/Config/Helpdesk.php
 * Os valores vêm das variáveis de ambiente definidas no docker-compose.yml.
 * NÃO usar em produção.
 */

namespace Config;

use CodeIgniter\Config\BaseConfig;

class Helpdesk extends BaseConfig
{
    const DB_HOST = HDZ_DEV_DB_HOST;
    const DB_USER = HDZ_DEV_DB_USER;
    const DB_PASSWORD = HDZ_DEV_DB_PASSWORD;
    const DB_NAME = HDZ_DEV_DB_NAME;
    const DB_PREFIX = 'hdz_';
    const DB_PORT = 3306;
    const SITE_URL = HDZ_DEV_SITE_URL;
    const UPLOAD_PATH = FCPATH . 'upload';
    const DEFAULT_LANG = 'en';
    const STAFF_URI = 'staff';
}

// Constantes lidas do ambiente (com valores por omissão para correr sem Docker)
defined('HDZ_DEV_DB_HOST') || define('HDZ_DEV_DB_HOST', getenv('HDZ_DB_HOST') ?: '127.0.0.1');
defined('HDZ_DEV_DB_USER') || define('HDZ_DEV_DB_USER', getenv('HDZ_DB_USER') ?: 'hdz');
defined('HDZ_DEV_DB_PASSWORD') || define('HDZ_DEV_DB_PASSWORD', getenv('HDZ_DB_PASSWORD') ?: 'hdzdev');
defined('HDZ_DEV_DB_NAME') || define('HDZ_DEV_DB_NAME', getenv('HDZ_DB_NAME') ?: 'helpdeskz');
defined('HDZ_DEV_SITE_URL') || define('HDZ_DEV_SITE_URL', getenv('HDZ_SITE_URL') ?: 'http://localhost:8080');
