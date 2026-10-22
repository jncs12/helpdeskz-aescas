<?php
/**
 * @var $this \CodeIgniter\View\View
 */
$this->extend('client/template');
$this->section('window_title');
echo lang('Client.login.resetTitle');
$this->endSection();
$this->section('content');
?>
<div class="container mt-5">
    <h1 class="heading mb-5">
        <?php echo lang('Client.login.resetTitle');?>
    </h1>
    <div class="mb-3">
        <?php echo lang('Client.login.resetDescription');?>
    </div>
    <?php
    if(isset($error_msg)){
        echo '<div class="alert alert-danger">'.$error_msg.'</div>';
    }
    echo form_open('',['autocomplete' => 'off'],['do'=>'submit']);
    ?>
    <div class="row">
        <div class="col-lg-6">
            <div class="form-group">
                <label><?php echo lang('Client.form.newPassword');?></label>
                <input type="password" name="new_password" class="form-control" autocomplete="new-password" minlength="8" required>
            </div>
            <div class="form-group">
                <label><?php echo lang('Client.form.newPassword');?> (<?php echo lang('Client.form.confirm');?>)</label>
                <input type="password" name="new_password2" class="form-control" autocomplete="new-password" minlength="8" required>
            </div>
            <div class="form-group">
                <button class="btn btn-primary"><?php echo lang('Client.form.submit');?></button>
            </div>
        </div>
    </div>
    <?php echo form_close();?>
</div>
<?php
$this->endSection();
