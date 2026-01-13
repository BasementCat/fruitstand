(function() {
    window.addEventListener('load', function() {
        // Autoselect timezone
        (function() {
            let tz;
            try {
                tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
            } catch (e) {
                return;
            }
            document.querySelectorAll('[name=timezone]').forEach(function(e) {
                switch (e.tagName) {
                    case 'INPUT':
                        if (!e.value) {
                            e.value = tz;
                        }
                        break;
                    case 'SELECT':
                        // value is probably always something, so instead ensure nothing was pre-selected
                        if (!e.querySelector('option[selected]')) {
                            e.value = tz;
                        }
                        break;
                }
            });
        })();

        // Method URLs
        (function() {
            document.querySelectorAll('a[data-link-method]').forEach(function(e) {
                console.log(e.dataset.linkMethod, e);
                const f = document.createElement('form');
                f.method = e.dataset.linkMethod;
                f.action = e.href;
                document.body.appendChild(f);
                e.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    f.submit();
                });
            });
        })();
    });
})();