/*
 * Impede a submissão repetida de formulários marcados com data-submit-once.
 *
 * Problema: abrir um ticket ou responder pode demorar alguns segundos (upload de anexos,
 * envio de emails). Quem volta a carregar em «Enviar» faz o navegador cancelar o primeiro
 * pedido e enviar outro — mas o servidor processa os dois e ficam tickets duplicados.
 *
 * Depois do primeiro envio, o botão mostra «A enviar…» e os envios seguintes são ignorados.
 * O botão NÃO é desativado com `disabled` (isso tiraria o seu valor dos dados enviados).
 * O servidor tem a sua própria proteção contra duplicados; isto é só a primeira barreira.
 */
(function () {
    'use strict';

    // Ao fim deste tempo o formulário volta a aceitar envios (ex.: a ligação caiu e é
    // preciso tentar outra vez). Se o primeiro pedido afinal chegou, o servidor não duplica.
    var UNLOCK_AFTER_MS = 30000;

    function submitButtons(form) {
        return form.querySelectorAll('button:not([type="button"]):not([type="reset"]), input[type="submit"]');
    }

    function lock(form) {
        form.setAttribute('data-submitting', '1');
        submitButtons(form).forEach(function (btn) {
            btn.classList.add('disabled');
            btn.setAttribute('aria-disabled', 'true');
            var sending = form.getAttribute('data-submit-once');
            if (sending && btn.tagName === 'BUTTON') {
                if (!btn.hasAttribute('data-original-html')) {
                    btn.setAttribute('data-original-html', btn.innerHTML);
                }
                btn.textContent = sending;
            }
        });
        form._submitOnceTimer = setTimeout(function () { unlock(form); }, UNLOCK_AFTER_MS);
    }

    function unlock(form) {
        clearTimeout(form._submitOnceTimer);
        form.removeAttribute('data-submitting');
        submitButtons(form).forEach(function (btn) {
            btn.classList.remove('disabled');
            btn.removeAttribute('aria-disabled');
            if (btn.hasAttribute('data-original-html')) {
                btn.innerHTML = btn.getAttribute('data-original-html');
                btn.removeAttribute('data-original-html');
            }
        });
    }

    // Fase de captura: corre antes de outros handlers e apanha todos os formulários marcados.
    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!form || !form.hasAttribute || !form.hasAttribute('data-submit-once')) {
            return;
        }
        if (form.getAttribute('data-submitting') === '1') {
            event.preventDefault();
            event.stopImmediatePropagation();
            return;
        }
        // Só bloqueia depois de os outros handlers terem tido oportunidade de cancelar
        // o envio (ex.: confirmações); por isso decide no fim da fase de propagação.
        setTimeout(function () {
            if (!event.defaultPrevented) {
                lock(form);
            }
        }, 0);
    }, true);

    // Ao voltar a esta página com «Retroceder», o navegador pode mostrá-la tal como estava
    // (cache bfcache): repõe os formulários para poderem ser usados.
    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            document.querySelectorAll('form[data-submitting]').forEach(unlock);
        }
    });
})();
