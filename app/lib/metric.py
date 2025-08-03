import typing as t

from flask import request


class Metric:
    _all_metrics: t.Optional[t.List[t.Self]] = None

    key: str = None
    name: str = None
    description: t.Optional[str] = None
    param: str = None
    format_description: str = None
    provides: t.Dict[str, str] = {}
    order: int = 100

    def __init__(self):
        self.raw = request.args.get(self.param) or None
        self.parsed = self.parse(self.raw)

    def parse(self, raw):
        return raw

    def get_data(self):
        if self.parsed is None:
            return {}
        if isinstance(self.parsed, dict):
            return self.parsed
        return {self.key: self.parsed}

    @classmethod
    def get_demo_inputs(cls):
        pass

    @classmethod
    def format_demo_inputs(cls, data):
        return None

    @classmethod
    def get_metric_classes(cls):
        if cls._all_metrics is None:
            cls._all_metrics = []
            queue = [cls]
            while queue:
                mc = queue.pop()
                if mc.key:
                    cls._all_metrics.append(mc)
                queue += mc.__subclasses__()
            cls._all_metrics = list(sorted(cls._all_metrics, key=lambda m: m.order))
        return list(cls._all_metrics)

    @classmethod
    def get_metrics(cls):
        out = {}
        for mc in cls.get_metric_classes():
            out.update(mc().get_data())
        return out

    @classmethod
    def get_all_demo_inputs(cls):
        out = {}
        for mc in cls.get_metric_classes():
            inputs = mc.get_demo_inputs()
            if inputs:
                out[mc.key] = (mc.name, mc.param, inputs)
        return out


class Battery(Metric):
    key = 'battery'
    name = 'Battery'
    description = "Battery statistics"
    param = 'batt'
    format_description = '"<type(lipo,nimh,alkaline,alkaline4,lithium,lithium4)>;<voltage>[;c]" - ex. "lipo;3.9", "lipo;3.9;c" (charging)'
    provides = {
        'min_v': "Minimum voltage (float)",
        'max_v': "Maximum voltage (float)",
        'voltage': "Current voltage (float)",
        'percent': "Current battery percentage (float, 0-1)",
        'type': "Battery type (str)",
        'charging': "Is charging (bool)",
    }
    order = 0

    def parse(self, raw):
        if raw:
            parts = raw.split(';')
            if len(parts) == 2:
                charging = False
                type_, voltage = parts
            elif len(parts) == 3:
                charging = True
                type_, voltage = parts[:2]
            else:
                return
            try:
                voltage = float(voltage)
                min_v, max_v = {
                    'lipo': (3.4, 4.2),
                    'nimh': (3.4, 4.8),
                    'alkaline': (3.4, 4.5),
                    'alkaline4': (3.4, 6),
                    'lithium': (3.4, 4.5),
                    'lithium4': (3.4, 6),
                }[type_]
                if type_.endswith('4'):
                    type_ = type_[:-1]
            except:
                return

            return {self.key: {
                'min_v': min_v,
                'max_v': max_v,
                'voltage': voltage,
                'percent': (voltage - min_v) / (max_v - min_v),
                'type': type_,
                'charging': charging,
            }}

    @classmethod
    def get_demo_inputs(cls):
        return {
            'type': {
                'label': "Battery Type",
                'type': 'select',
                'choices': {
                    'lipo': 'LiPo (4.2v)',
                    'nimh': 'NiMH (4, 4.8v)',
                    'alkaline': 'Alkaline (3, 4.5v)',
                    'alkaline4': 'Alkaline (4, 6v)',
                    'lithium': 'Lithium (3, 4.5v)',
                    'lithium4': 'Lithium (4, 6v)',
                },
                'default': 'lipo',
            },
            'voltage': {
                'label': "Voltage",
                'type': 'range',
                'min': 3.4,
                'max': 6,
                'step': 0.01,
                'default': 3.9,
            },
            'charging': {
                'label': "Is Charging",
                'type': 'checkbox',
                'default': False,
            }
        }

    @classmethod
    def format_demo_inputs(cls, data):
        out = [
            data['type'],
            data['voltage'],
            'c' if data['charging'] else None
        ]
        return ';'.join(map(str, filter(None, out)))


class Wifi(Metric):
    key = 'wifi'
    name = 'WiFi'
    description = "WiFi statistics"
    param = 'wifi'
    format_description = "WiFi signal strength, dBm"
    provides = {
        'dbm': "Signal strength",
        'bars': '"Bars" of signal strength',
    }
    order = 1

    def parse(self, raw):
        if raw:
            try:
                dbm = float(raw)
            except:
                return

            if dbm >= -30:
                bars = 4
            elif dbm >= -67:
                bars = 3
            elif dbm >= -70:
                bars = 2
            elif dbm >= -80:
                bars = 1
            elif dbm >= -90:
                bars = 0
            else:
                bars = -1

            return {
                self.key: {
                    'dbm': dbm,
                    'b': bars,
                }
            }

    @classmethod
    def get_demo_inputs(cls):
        return {
            'signal': {
                'label': "Signal Strength (dBm)",
                'type': 'range',
                'min': -100,
                'max': -10,
                'step': 0.1,
                'default': -71,
            },
        }

    @classmethod
    def format_demo_inputs(cls, data):
        return str(data['signal'])
