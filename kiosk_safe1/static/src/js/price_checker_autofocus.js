odoo.define('price_checker_kiosk.autofocus', function (require) {
    "use strict";
    function focusAndBind() {
        let tries = 0;
        const timer = setInterval(() => {
            tries += 1;
            const input = document.querySelector('.o_price_checker_form input[name="barcode"]');
            if (input) {
                input.focus();
                input.select();
                input.addEventListener('keydown', (ev) => {
                    if (ev.key === 'Enter') {
                        ev.preventDefault();
                        const btn = document.querySelector('.o_price_checker_form button[name="action_check"]');
                        if (btn) btn.click();
                    }
                });
                clearInterval(timer);
            }
            if (tries > 50) clearInterval(timer);
        }, 100);
    }
    document.addEventListener('DOMContentLoaded', () => {
        focusAndBind();
        const obs = new MutationObserver(() => focusAndBind());
        obs.observe(document.body, { childList: true, subtree: true });
    });
});
