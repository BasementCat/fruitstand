var fruitstand = {
    modules: [],

    init: function() {
        window.addEventListener('load', this.onLoad.bind(this));
    },

    onLoad: function() {
        this.modules.forEach(m => {
            if (m.init && !m.init()) return;
            if (m.registerEvents) m.registerEvents();
        });
    },

    module: function(m) {
        this.modules.push(m);
    }
};
fruitstand.init();


// Autoselect timezone
fruitstand.module({
    els: null,
    tz: null,

    init: function() {
        try {
            this.tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
        } catch (e) {
            return false;
        }
        this.els = document.querySelectorAll('[name=timezone]');
        this.els.forEach(this.setInputState.bind(this));
    },

    setInputState: function(el) {
        switch (el.tagName) {
            case 'INPUT':
                if (!el.value) {
                    el.value = this.tz;
                }
                break;
            case 'SELECT':
                // value is probably always something, so instead ensure nothing was pre-selected
                if (!el.querySelector('option[selected]')) {
                    el.value = this.tz;
                }
                break;
        }
    }
});


// Method links
fruitstand.module({
    els: null,

    init: function() {
        this.els = document.querySelectorAll('a[data-link-method]');
        return true;
    },

    registerEvents: function() {
        this.els.forEach(el => this.createFormForLink.bind(this));
    },

    createFormForLink: function(el) {
        const f = document.createElement('form');
        f.method = el.dataset.linkMethod;
        f.action = el.href;
        document.body.appendChild(f);
        el.addEventListener('click', this.handleLinkClick.bind(this, f));
    },

    handleLinkClick: function(f, e) {
        e.preventDefault();
        e.stopPropagation();
        f.submit();
    }
});


// Reveal
fruitstand.module({
    init: function() {
        document.querySelectorAll('[data-reveal]').forEach(this.setupReveal.bind(this))
    },

    setupReveal: function(el) {
        const hidden = document.createElement('span');
        hidden.innerText = '********';

        const data = document.createElement('span');
        data.innerText = el.dataset.reveal;
        data.style.display = 'none';

        const eye = document.createElement('a');
        eye.title = "Show/Hide";
        eye.href = "#";
        eye.style.textDecoration = 'none';
        eye.innerHTML = '&nbsp;<i class="fas fa-eye"></i><span class="sr-only">Show/Hide</span>';

        el.appendChild(hidden);
        el.appendChild(data);
        el.appendChild(eye);

        eye.addEventListener('click', this.toggle.bind(this, el, hidden, data, eye));
    },

    toggle: function(el, hidden, data, eye, ev) {
        ev.stopPropagation();
        ev.preventDefault();
        const i = eye.querySelector('i');

        if (el.dataset.isVisible) {
            hidden.style.display = 'inline';
            data.style.display = 'none';
            i.classList.add('fa-eye');
            i.classList.remove('fa-eye-slash');
            delete el.dataset.isVisible;
        } else {
            hidden.style.display = 'none';
            data.style.display = 'inline';
            i.classList.add('fa-eye-slash');
            i.classList.remove('fa-eye');
            el.dataset.isVisible = true;
        }
    },
})