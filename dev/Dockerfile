# Ambiente de desenvolvimento HelpDeskZ — espelha a produção (PHP 8.4 + Apache 2.4)
FROM php:8.4-apache

# Extensões exigidas pelo HelpDeskZ: intl, fileinfo, iconv, mbstring, mysqli, imap
# (imap saiu do core no PHP 8.4 → instala-se a partir do PECL)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        libicu-dev libonig-dev libc-client-dev libkrb5-dev libzip-dev unzip git \
 && docker-php-ext-install intl mysqli \
 && pecl install imap \
 && docker-php-ext-enable imap \
 && a2enmod rewrite \
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
