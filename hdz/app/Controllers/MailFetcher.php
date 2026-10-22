<?php
/**
 * @package EvolutionScript
 * @author: EvolutionScript S.A.C.
 * @Copyright (c) 2010 - 2020, EvolutionScript.com
 * @link http://www.evolutionscript.com
 */

namespace App\Controllers;

class MailFetcher extends BaseController
{
    public function imap()
    {
        $mailFetcherLib = new \App\Libraries\MailFetcher();
        return $mailFetcherLib->parse_imap();
    }

    public function pipe()
    {
        // O piping é sempre invocado pelo servidor de email via pipe.php (CLI).
        // Pela web não faz sentido e apenas criaria ficheiros temporários vazios.
        if (!is_cli()) {
            throw \CodeIgniter\Exceptions\PageNotFoundException::forPageNotFound();
        }
        $mailFetcherLib = new \App\Libraries\MailFetcher();
        return $mailFetcherLib->parse_pipe();
    }
}