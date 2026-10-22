<?php
/**
 * @package EvolutionScript
 * @author: EvolutionScript S.A.C.
 * @Copyright (c) 2010 - 2020, EvolutionScript.com
 * @link http://www.evolutionscript.com
 */

namespace App\Controllers;


use App\Libraries\reCAPTCHA;
use Config\Services;

class UserAuth extends BaseController
{
    public function login()
    {
        if($this->request->getPost('do') == 'submit')
        {
            $validation = Services::validation();
            $validation->setRules(
                [
                    'email' => 'required|valid_email',
                    'password' => 'required',
                ]
            );

            // Limite de tentativas falhadas por IP (mesma configuração do painel de staff)
            $staffLib = Services::staff();
            $attemptKey = 'client:' . $this->request->getIPAddress();
            if($staffLib->isLocked($attemptKey)){
                $error_msg = lang_replace('Client.error.tooManyAttempts', [
                    '%minutes%' => $this->settings->config('login_attempt_minutes')
                ]);
            }elseif($validation->withRequest($this->request)->run() == false){
                $error_msg = lang('Client.error.invalidEmailPassword');
            }elseif(!$client_data = $this->client->getRow([
                'email' => $this->request->getPost('email'),
                'status'=>1
            ])){
                $staffLib->addLoginAttempt($attemptKey);
                $error_msg = lang('Client.error.invalidEmailPassword');
            }else{
                if(!password_verify($this->request->getPost('password'), $client_data->password)){
                    $staffLib->addLoginAttempt($attemptKey);
                    $error_msg = lang('Client.error.invalidEmailPassword');
                }else{
                    $this->client->login($client_data->id, $client_data->password);
                    return redirect()->route('view_tickets');
                }
            }

        }
        return view('client/login',[
            'error_msg' => isset($error_msg) ? $error_msg : null
        ]);
    }

    public function resetPassword($client_id, $expires, $signature)
    {
        if(!$client_data = $this->client->verifyResetLink($client_id, $expires, $signature)){
            return view('client/error', [
                'title' => lang('Client.login.resetInvalidTitle'),
                'body' => lang('Client.login.resetInvalid'),
                'footer' => '<a href="'.site_url(route_to('forgot_password')).'">'.lang('Client.login.forgotPassword').'</a>'
            ]);
        }
        if($this->request->getPost('do') == 'submit'){
            $validation = Services::validation();
            $validation->setRules([
                'new_password' => 'required|min_length[8]',
                'new_password2' => 'matches[new_password]'
            ],[
                'new_password' => [
                    'required' => lang('Client.error.enterPassword'),
                    'min_length' => lang('Client.error.passwordTooShort'),
                ],
                'new_password2' => [
                    'matches' => lang('Client.error.passwordsNotMatches'),
                ]
            ]);
            if($validation->withRequest($this->request)->run() == false){
                $error_msg = $validation->listErrors();
            }else{
                $this->client->setPassword($client_data->id, $this->request->getPost('new_password'));
                $this->session->setFlashdata('form_success', lang('Client.login.passwordChanged'));
                return redirect()->route('login');
            }
        }
        return view('client/reset_password', [
            'error_msg' => isset($error_msg) ? $error_msg : null,
        ]);
    }

    public function forgot()
    {
        $reCAPTCHA = new reCAPTCHA();
        if($this->request->getPost('do') == 'submit')
        {
            $validation = Services::validation();
            $validation->setRule('email','email','required|valid_email');
            if(!$reCAPTCHA->validate()){
                $error_msg = lang('Client.error.invalidCaptcha');
            }elseif($validation->withRequest($this->request)->run() == false) {
                $error_msg = lang('Client.error.enterValidEmail');
            }else{
                // A resposta é igual quer o email exista quer não (evita descobrir contas)
                if($client_data = $this->client->getRow(['email' => $this->request->getPost('email'), 'status' => 1])){
                    $this->client->recoverPassword($client_data);
                }
                $this->session->setFlashdata('form_success', lang('Client.login.resetLinkSent'));
                return redirect()->route('forgot_password');
            }
        }
        return view('client/forgot', [
            'error_msg' => isset($error_msg) ? $error_msg : null,
            'recaptcha' => $reCAPTCHA->display()
        ]);
    }

    public function profile()
    {
        $validation = Services::validation();
        if($this->request->getPost('do') == 'general'){
            $validation->setRule('fullname','fullname','required',[
                'required' => lang('Client.error.enterFullName')
            ]);
            if($this->request->getPost('email') != $this->client->getData('email')){
                $validation->setRule('email','email','required|valid_email|is_unique[users.email]',[
                    'required' => lang('Client.error.enterValidEmail'),
                    'valid_email' => lang('Client.error.enterValidEmail'),
                    'is_unique' => lang('Client.error.emailUsed')
                ]);
            }
            if($validation->withRequest($this->request)->run() == false){
                $error_msg = $validation->listErrors();
            }else{
                $timezone_user = in_array($this->request->getPost('timezone'), timezone_identifiers_list()) ? $this->request->getPost('timezone') : '';
                $this->client->update([
                    'email' => $this->request->getPost('email'),
                    'fullname' => esc($this->request->getPost('fullname')),
                    'timezone' => $timezone_user
                ]);
                $this->session->setFlashdata('form_success',lang('Client.account.profileUpdated'));
                return redirect()->route('profile');
            }
        }elseif ($this->request->getPost('do') == 'password'){
            $validation->setRules([
                'current_password' => 'required',
                'new_password' => 'required',
                'new_password2' => 'matches[new_password]'
            ],[
                'current_password' => [
                    'required' => lang('Client.error.enterExistingPassword')
                ],
                'new_password' => [
                    'required' => lang('Client.error.enterNewPassword')
                ],
                'new_password2' => [
                    'matches' => lang('Client.error.passwordsNotMatches')
                ]
            ]);
            if($validation->withRequest($this->request)->run() == FALSE){
                $error_msg = $validation->listErrors();
            }elseif(!password_verify($this->request->getPost('current_password'), $this->client->getData('password'))) {
                $error_msg = lang('Client.error.wrongExistingPassword');
            }else{
                $password = password_hash($this->request->getPost('new_password'), PASSWORD_BCRYPT);
                $this->client->update([
                    'password' => $password
                ]);
                $this->client->createSession($this->client->getData('id'), $password);
                $this->session->setFlashdata('form_success',lang('Client.account.passwordUpdated'));
                return redirect()->route('profile');
            }
        }
        return view('client/profile',[
            'error_msg' => isset($error_msg) ? $error_msg : null
        ]);
    }

    public function logout()
    {
        return $this->client->logout();
    }
}