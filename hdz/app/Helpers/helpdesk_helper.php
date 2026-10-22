<?php
function set_timezone($timezone)
{
    if ($timezone != '' && in_array($timezone, timezone_identifiers_list())) {
        date_default_timezone_set($timezone);
    }
}
function site_logo()
{
    return \Config\Services::settings()->getLogo();
}

function site_config($var)
{
    return \Config\Services::settings()->config($var);
}

function client_online()
{
    return \Config\Services::client()->isOnline();
}

function client_data($var)
{
    return \Config\Services::client()->getData($var);
}

function staff_data($var)
{
    return \Config\Services::staff()->getData($var);
}

function staff_avatar($avatarFile = '')
{
    $default_avatar = base_url('assets/helpdeskz/images/agent.jpg');
    if ($avatarFile == '') {
        return $default_avatar;
    }
    $upload_avatar = \Config\Helpdesk::UPLOAD_PATH . DIRECTORY_SEPARATOR . $avatarFile;
    if (!file_exists($upload_avatar)) {
        return $default_avatar;
    }
    return base_url('upload/' . $avatarFile);
}

function user_avatar($avatarFile = '')
{
    $default_avatar = base_url('assets/helpdeskz/images/user.jpg');
    if ($avatarFile == '') {
        return $default_avatar;
    }
    $upload_avatar = \Config\Helpdesk::UPLOAD_PATH . DIRECTORY_SEPARATOR . $avatarFile;
    if (!file_exists($upload_avatar)) {
        return $default_avatar;
    }
    return base_url('upload/' . $avatarFile);
}

function staff_info($staff_id)
{
    static $staffList;
    if ($staff_id == 0) {
        return ['fullname' => '-', 'avatar' => staff_avatar()];
    }
    if (!is_array($staffList) || !isset($staffList[$staff_id])) {
        if (!$data = \Config\Services::staff()->getRow(['id' => $staff_id], 'fullname, avatar')) {
            return $staffList[$staff_id] = ['fullname' => '-', 'avatar' => staff_avatar()];
        } else {
            return $staffList[$staff_id] = ['fullname' => $data->fullname, 'avatar' => staff_avatar($data->avatar)];
        }
    } else {
        return $staffList[$staff_id];
    }
}

function uri_page()
{
    static $page;
    if (!$page) {
        $uri = \Config\Services::uri();
        $page = $uri->getSegment(2);
    }
    return $page;
}
/*
 * Knowledge Base
 */
function kb_parents($parent_id)
{
    return \Config\Services::kb()->getParents($parent_id);
}
function kb_categories($parent = 0, $public = true)
{
    return \Config\Services::kb()->getCategories($parent, $public);
}
function kb_count_articles($category_id, $public = true)
{
    return \Config\Services::kb()->countArticles($category_id, $public);
}

function kb_count_articles_category($category_id, $public = true)
{
    return \Config\Services::kb()->totalArticlesInCat($category_id, $public);
}

function kb_cat_move_link($category_id, $parent)
{
    return \Config\Services::kb()->moveUpOrDownLink($category_id, $parent);
}

function kb_articles_category($category_id, $public = true)
{
    return \Config\Services::kb()->articlesUnderCategory($category_id, $public);
}

function kb_articles($category_id, $public = true)
{
    return \Config\Services::kb()->getArticles($category_id, $public);
}

function kb_popular($public = 1)
{
    return \Config\Services::kb()->popularArticles($public);
}

function kb_newest($public = 1)
{
    return \Config\Services::kb()->newestArticles($public);
}

function resume_content($text, $chars, $clean_html = true)
{
    $text = (string)$text;
    if ($clean_html) {
        $text = strip_tags($text);
        // Converte entidades antes de cortar, para não partir "&amp;" a meio
        $text = html_entity_decode($text, ENT_QUOTES | ENT_HTML5, 'UTF-8');
    }
    if (mb_strlen($text) > $chars) {
        $text = mb_substr($text, 0, ($chars - 3)) . '...';
    }
    // O resultado é sempre texto simples, pronto a imprimir em HTML
    return $clean_html ? hdz_e($text) : $text;
}

/**
 * Escapa texto para saída em HTML (conteúdo e atributos).
 * Não volta a codificar entidades já existentes: parte dos dados antigos
 * foi gravada já escapada (esc() à entrada) e assim não aparece "&amp;amp;".
 */
function hdz_e($value): string
{
    return htmlspecialchars((string)$value, ENT_QUOTES | ENT_SUBSTITUTE | ENT_HTML5, 'UTF-8', false);
}

/**
 * Limpa HTML não confiável (mensagens, artigos, respostas) com o HTMLPurifier,
 * removendo scripts, handlers on*, iframes, etc. Mantém a formatação comum.
 */
function hdz_purify($html): string
{
    static $purifier = null;
    if ($purifier === null) {
        $config = \HTMLPurifier_Config::createDefault();
        $cacheDir = WRITEPATH . 'cache' . DIRECTORY_SEPARATOR . 'htmlpurifier';
        if (!is_dir($cacheDir)) {
            @mkdir($cacheDir, 0775, true);
        }
        if (is_dir($cacheDir) && is_writable($cacheDir)) {
            $config->set('Cache.SerializerPath', $cacheDir);
        } else {
            $config->set('Cache.DefinitionImpl', null);
        }
        $config->set('HTML.TargetBlank', true);
        $config->set('URI.AllowedSchemes', ['http' => true, 'https' => true, 'mailto' => true, 'data' => true, 'tel' => true]);
        $config->set('Attr.AllowedFrameTargets', ['_blank']);
        $purifier = new \HTMLPurifier($config);
    }
    return $purifier->purify((string)$html);
}

/**
 * Converte texto simples em HTML seguro com quebras de linha.
 */
function hdz_nl2br($text): string
{
    return nl2br(hdz_e($text));
}

#Language
function lang_replace($var, $field, $value = null)
{
    if (!is_array($field)) {
        $field = array($field => $value);
    }
    return str_replace(array_keys($field), array_values($field), lang($var));
}
#Attachments
function article_files($article_id)
{
    return \Config\Services::attachments()->getList(['article_id' => $article_id]);
}

function ticket_files($ticket_id, $msg_id)
{
    return \Config\Services::attachments()->getList(['ticket_id' => $ticket_id, 'msg_id' => $msg_id]);
}

#Date
function dateFormat($data)
{
    return date(site_config('date_format'), $data);
}

#tickets
function count_tickets($status)
{
    return \Config\Services::staff()->countTicketsByStatus($status);
}

function sort_link($id, $string)
{
    $url = current_url(true);
    $url = parse_url($url);
    $query = (isset($url['query'])) ? $url['query'] : '';
    parse_str($query, $output);
    if (isset($output['sort']) && $output['sort'] == $id) {
        if (isset($output['order']) && $output['order'] == 'DESC') {
            $output['order'] = 'ASC';
            $icon = '<i class="fa fa-caret-down"></i></a>';
        } else {
            $output['order'] = 'DESC';
            $icon = '<i class="fa fa-caret-up"></i></a>';
        }
    } else {
        $output['order'] = 'DESC';
        $icon = '<i class="fa fa-sort"></i></a>';
    }
    $output['sort'] = $id;

    $query = http_build_query($output);
    return '<span data-href="' . current_url() . '?' . $query . '" class="pointer">' . $string . ' ' . $icon . '</span>';
}

function isOverdue($date, $status)
{
    return \Config\Services::tickets()->isOverdue($date, $status);
}

function time_ago($time, $staff = true)
{

    if (date("d-m-Y", $time) == date("d-m-Y")) {
        $lang = ($staff ? 'Admin.form.todayAt' : 'Client.todayAt');
        return lang_replace($lang, ['%date%' => date('h:i a', $time)]);
    } elseif (date("d-m-Y", $time) == date('d-m-Y', strtotime("+1 day ago"))) {
        $lang = ($staff ? 'Admin.form.yesterdayAt' : 'Client.yesterdayAt');
        return lang_replace($lang, ['%date%' => date('h:i a', $time)]);
    } else {
        return dateFormat($time);
    }
}

function count_status($status)
{
    return \Config\Services::tickets()->countStatus($status);
}

function max_file_size()
{
    static $file_size;
    if (!$file_size) {
        $max_upload = (int)(ini_get('upload_max_filesize'));
        $max_post = (int)(ini_get('post_max_size'));
        $memory_limit = (int)(ini_get('memory_limit'));
        $file_size = min($max_upload, $max_post, $memory_limit);
        $file_size = $file_size * 1024;
    }
    return $file_size;
}

function countDepartmentTickets($department_id)
{
    return \Config\Services::departments()->countTickets($department_id);
}

function countDepartmentAgents($department_id)
{
    return \Config\Services::departments()->countAgents($department_id);
}

function getDepartmentByID($department_id)
{
    return \Config\Services::departments()->getByID($department_id);
}

function getDepartments($onlyPublic = true)
{
    return ($onlyPublic === true)
        ? \Config\Services::departments()->getPublic()
        : \Config\Services::departments()->getAll();
}

function parseCustomFieldsForm($customField)
{
    $customFields = new \App\Libraries\CustomFields();
    return $customFields->parseForm($customField);
}

/*
 * -----------------------------------------
 * Encode/Decode data
 * -----------------------------------------
 */
function str_encode($str)
{
    if ($str == '') {
        return '';
    } else {
        $ascii = strrev(base64_encode(strrev($str)));
        $hex = '';
        for ($i = 0; $i < strlen($ascii); $i++) {
            $byte = strtoupper(dechex(ord($ascii[$i])));
            $byte = str_repeat('0', 2 - strlen($byte)) . $byte;
            $hex .= $byte;
        }
        return $hex;
    }
}

function str_decode($str)
{
    if ($str == '') {
        return '';
    } else {
        $hex = $str;
        $ascii = '';
        $hex = str_replace(" ", "", $hex);
        for ($i = 0; $i < strlen($hex); $i = $i + 2) {
            $ascii .= chr(hexdec(substr($hex, $i, 2)));
        }
        return strrev(base64_decode(strrev($ascii)));
    }
}
/**
 * unserialize() seguro: nunca instancia objetos (evita "PHP object injection").
 */
function hdz_unserialize($data)
{
    if (!is_string($data) || $data === '') {
        return false;
    }
    return @unserialize($data, ['allowed_classes' => false]);
}

/**
 * Cadeia aleatória criptograficamente segura (random_int), alfanumérica.
 * Substitui random_string() do CodeIgniter 4.1, que usa mt_rand/str_shuffle.
 */
function hdz_random_string(int $length = 32): string
{
    $pool = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ';
    $max = strlen($pool) - 1;
    $out = '';
    for ($i = 0; $i < $length; $i++) {
        $out .= $pool[random_int(0, $max)];
    }
    return $out;
}

/**
 * Segredo da instalação (para assinar links). Gerado na primeira utilização e
 * guardado em hdz/writable/hdz_secret.php (fora do alcance da web).
 */
function hdz_secret(): string
{
    static $secret = null;
    if ($secret !== null) {
        return $secret;
    }
    $file = WRITEPATH . 'hdz_secret.php';
    if (is_file($file)) {
        $value = include $file;
        if (is_string($value) && strlen($value) >= 32) {
            return $secret = $value;
        }
    }
    $secret = bin2hex(random_bytes(32));
    file_put_contents($file, "<?php\n// Gerado automaticamente. Não partilhar. Apagar invalida links pendentes.\nreturn '" . $secret . "';\n", LOCK_EX);
    @chmod($file, 0640);
    return $secret;
}
