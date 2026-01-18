(function() {
    class Control {
        constructor(id_key, config_key=null, dfl='') {
            this.id_key = id_key;
            this.config_key = config_key === false ? null : (config_key || id_key);
            this.el = this.find_el();
            this._value = null;
            this.on_change_cb = [];
            this.value = dfl;

            if (this.el) {
                this.el.addEventListener('change', e => {
                    if (this.el.type == 'checkbox') {
                        this.value = !!this.el.checked;
                    } else {
                        this.value = this.el.value;
                    }
                });
            }
        }

        get dom_id() {
            return 'dd_' + this.id_key;
        }

        find_el() {
            return document.getElementById(this.dom_id);
        }

        get value() {
            return this._value;
        }

        update_field() {
            if (this.el) {
                if (this.el.type == 'checkbox') {
                    this.el.checked = !!this._value;
                } else {
                    this.el.value = this._value;
                }
            }
        }

        set value(v) {
            this._value = v;
            // console.debug("Set field %s value to %s", this.id_key, v);
            this.update_field();
            this.on_change_cb.forEach(cb => cb(this));
        }

        get config_value() {
            let out = {};
            if (this.config_key) {
                out[this.config_key] = this.value;
            }
            return out;
        }

        on_change(callback) {
            this.on_change_cb.push(callback);
        }
    }

    class PLSControl extends Control {
        set value(v) {
            super.value = v;
            this._pls_id = 0;
            this._scr_id = 0;
            v.split(';').forEach(p => {
                let [k, v] = p.split('-');
                v = parseInt(v);
                switch (k) {
                    case 'p':
                        this._pls_id = v;
                        break;
                    case 's':
                        this._scr_id = v;
                        break;
                }
            });
        }

        get value() {
            return 'p-' + this._pls_id + ';s-' + this._scr_id;
        }

        get config_value() {
            let out = {
                'playlist_id': this._pls_id,
                'playlist_screen_id': this._scr_id,
            };
            Object.assign(out, super.config_value);
            return out;
        }
    }

    class Metric extends Control {
        constructor(key, input_name, config_key=null, dfl='') {
            super('metric_' + key + '_' + input_name, config_key, dfl);
            this.is_metric = true;
            this.key = key;
            this.input_name = input_name;
            // this.enabled_el = document.getElementById('dd_metric_' + this.key + '_enabled');
            this.output_el = document.getElementById('dd_' + this.id_key + '_value');
            this.value = this.value;  // force an update
        }

        update_field() {
            super.update_field();
            if (this.output_el) {
                this.output_el.innerText = this.value;
            }
        }

        apply_to_form(formdata) {
            const form_name = this.key + ';' + this.input_name;
            let val = null;
            if (this.el.type == 'checkbox') {
                if (this.el.checked) {
                    val = this.el.value;
                }
            } else {
                val = this.el.value;
            }
            if (val !== null) {
                formdata.append(form_name, val);
            }
        }
    }

    class Config {
        constructor(controls) {
            this.controls = controls;
            this.default_config = {};
            controls.forEach(c => {
                Object.assign(this.default_config, c.config_value);
                c.on_change(this.field_changed.bind(this));
            });
            this.config = {};
            Object.assign(this.config, this.default_config);
            this._save_timeout = null;
            this.on_update_cb = [];
            this.load();
        }

        on_update(callback) {
            this.on_update_cb.push(callback);
        }

        do_on_update() {
            this.on_update_cb.forEach(c => c());
        }

        field_changed(field) {
            Object.assign(this.config, field.config_value);
            this.save();
        }

        reset() {
            Object.assign(this.config, this.default_config);
            this.save();
            this.update_fields();
            this.do_on_update();
        }

        update_fields() {
            this.controls.forEach(c => {
                if (c.config_key && this.config.hasOwnProperty(c.config_key)) {
                    c.value = this.config[c.config_key];
                }
            });
        }

        save() {
            if (this._save_timeout) {
                window.clearTimeout(this._save_timeout);
            }
            this._save_timeout = window.setTimeout(this._do_save.bind(this), 100);
        }

        _do_save() {
            this._save_timeout = null;
            window.localStorage.setItem('fs_demo_data', JSON.stringify(this.config));
            this.do_on_update();
        }

        load() {
            let data_str = window.localStorage.getItem('fs_demo_data');
            if (data_str) {
                try {
                    let data_obj = JSON.parse(data_str);
                    if (data_obj) {
                        Object.assign(this.config, data_obj);
                        this.update_fields();
                    }
                } catch (e) {}
            }
            this.do_on_update();
        }
    }

    class Renderer {
        constructor(controls, config, iframe_url, iframe) {
            this.controls = controls;
            this.config = config;
            this.iframe_url = iframe_url;
            this.iframe = iframe;
            this.width = this.height = 0;
            this._is_rendering = false;
            this.iframe.addEventListener('load', e => this._is_rendering = false);
            config.on_update(this.maybe_autorender.bind(this));
        }

        async get_metric_qs() {
            let formdata = new FormData();
            this.controls.forEach(c => {
                if (c.apply_to_form) {
                    c.apply_to_form(formdata);
                }
            });
            let resp = await fetch(dd_config.urls.params, {'method': 'POST', 'body': formdata});
            let qs = await resp.text();
            return qs;
        }

        get_params_qs() {
            let parts = [
                ['k', this.config.config['key']],
                ['sk', this.config.config['sk_sel'] || this.config.config['sk']],
                ['cs', this.config.config['color_spec']],
                ['ds', this.config.config['display_spec']],
                ['debug_playlist_id', this.config.config['playlist_id']],
                ['debug_playlist_screen_id', this.config.config['playlist_screen_id']],
            ];
            if (this.config.config['size']) {
                const [w, h] = this.config.config['size'].split('x');
                this.width = w;
                this.height = h;
                parts.push(['w', w]);
                parts.push(['h', h]);
            } else {
                parts.push(['w', this.config.config['width']]);
                parts.push(['h', this.config.config['height']]);
                this.width = this.config.config['width'];
                this.height = this.config.config['height'];
            }
            return parts.filter(p => p[1]).map(p => p.join('=')).join('&');
        }

        async build_url() {
            let met_qs = await this.get_metric_qs();
            let par_qs = this.get_params_qs();

            return dd_config.urls.base + par_qs + '&' + met_qs;
        }

        async render() {
            if (this._is_rendering) return;
            this._is_rendering = true;
            const url = await this.build_url();
            this.iframe_url.value = url;
            this.iframe.width = this.width;
            this.iframe.height = this.height;
            this.iframe.src = url;
        }

        async maybe_autorender() {
            if (this.config.config['autoupdate']) {
                await this.render();
            }
        }
    }

    const b_update = new Control('update', false);
    const b_reset = new Control('reset', false);
    const c_iframe_url = new Control('iframe_url', false);
    const controls = [
        // url
        c_iframe_url,
        // arguments
        new Control('key', null, 'demo-display'),
        new PLSControl('playlist_screen', null, 'pl-0;s-0'),
        new Control('size'),
        new Control('width', null, 800),
        new Control('height', null, 480),
        new Control('color_spec', null, '1b'),
        new Control('display_spec', null, 'static'),
        new Control('sk_sel'),
        new Control('sk'),
        // additional controls
        b_update,
        b_reset,
        new Control('autoupdate'),
    ];
    // metrics
    let seen_metrics = [];
    dd_config.metrics.forEach(m => {
        controls.push(new Metric(m.key, m.input_name, null, m.default));
        if (!seen_metrics.includes(m.key)) {
            seen_metrics.push(m.key);
            controls.push(new Control('metric_' + m.key + '_enabled', null, true));
        }
    })

    const config = new Config(controls);
    const renderer = new Renderer(
        controls,
        config,
        c_iframe_url,
        document.getElementById('dd_iframe'),
    );

    b_reset.el.addEventListener('click', config.reset.bind(config));
    b_update.el.addEventListener('click', renderer.render.bind(renderer));

    c_iframe_url.on_change(f => document.getElementById('dd_iframe_url_open').href = f.value);
    document.getElementById('dd_iframe_url_copy').addEventListener('click', e => navigator.clipboard.writeText(c_iframe_url.value));
})();