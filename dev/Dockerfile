# Ambiente de desenvolvimento HelpDeskZ — espelha a produção (PHP 8.4 + Apache 2.4)
# Debian 12 «bookworm»: a imagem predefinida (Debian 13 «trixie») já não tem a
# biblioteca libc-client de que a extensão imap precisa. Tem versão arm64 (Apple Silicon).
FROM php:8.4-apache-bookworm

# Extensões exigidas pelo HelpDeskZ: intl, fileinfo, iconv, mbstring, mysqli, imap
# (imap saiu do core no PHP 8.4 → PECL; o printf aceita as opções predefinidas:
#  suporte Kerberos e SSL)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libicu-dev libonig-dev libc-client2007e-dev libkrb5-dev libssl-dev libzip-dev unzip git \
 && docker-php-ext-install intl mysqli \
 && printf "\n\n" | pecl install imap \
 && docker-php-ext-enable imap \
 && a2enmod rewrite headers \
 && rm -rf /var/lib/apt/lists/*

# Composer (para gerir dependências em fases seguintes)
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Configuração PHP de desenvolvimento: mostra todos os erros e avisos
RUN cp "$PHP_INI_DIR/php.ini-development" "$PHP_INI_DIR/php.ini" \
 && { echo 'upload_max_filesize=20M'; echo 'post_max_size=25M'; echo 'date.timezone=Europe/Lisbon'; } \
    > "$PHP_INI_DIR/conf.d/helpdeskz.ini"

# Permitir .htaccess
RUN sed -ri 's!AllowOverride None!AllowOverride All!g' /etc/apache2/apache2.conf

WORKDIR /var/www/html
