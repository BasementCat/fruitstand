from flask import request


class Metric:
    _all_metrics = None

    param = None
    key = None
    datatype = float
    title = None

    def __init__(self, metrics):
        self.metrics = metrics
        self.raw = request.args.get(self.param)
        self.setup()
        self.parsed = self.parse_value(self.raw)

    def setup(self):
        pass

    def get_data(self):
        if self.raw is None:
            return {}
        return {(self.key or self.param): self.parsed}

    def __call__(self):
        out = self.get_data()
        if out:
            return out
        return {}

    def parse_value(self, value):
        return self._cast(self._parse(value))

    def _cast(self, value):
        if value is not None:
            return self.datatype(value)

    def _parse(self, value):
        return value

    @classmethod
    def get_title(cls):
        return cls.title or cls.__name__

    @classmethod
    def get_demo_config(self):
        pass

    @classmethod
    def get_metric_classes(cls):
        if cls._all_metrics is None:
            cls._all_metrics = []
            queue = [cls]
            while queue:
                mc = queue.pop()
                if mc.param:
                    cls._all_metrics.append(mc)
                queue += mc.__subclasses__()
        return list(cls._all_metrics)

    @classmethod
    def get_metrics(cls):
        out = {}
        for mc in cls.get_metric_classes():
            met = mc(out)
            out.update(met())
        return out

    @classmethod
    def get_all_demo_config(cls):
        out = {}
        for mc in cls.get_metric_classes():
            out[mc.param] = {'param': mc.param, 'datatype': mc.datatype.__name__, 'title': mc.get_title()}
            out[mc.param].update(mc.get_demo_config() or {})
        return out



class Battery(Metric):
    param = 'batt'

    def setup(self):
        super().setup()
        self.maxv = float(request.args.get('batt_max', 4.2))
        self.minv = float(request.args.get('batt_min', 3.4))

    def get_data(self):
        if self.parsed:
            return {
                'batt': {
                    'v': self.parsed,
                    'p': (self.parsed - self.minv) / (self.maxv - self.minv),
                    'c': bool(int(request.args.get('batt_chg', 0))),
                }
            }

    @classmethod
    def get_demo_config(cls):
        return {
            'type': 'range',
            # TODO: alt. inputs
            'min': 3.4,
            'max': 4.2,
            'step': 0.01,
            'default': 3.7,
            'enabled': True,
        }


class BaseTemperature(Metric):
    def _parse(self, value):
        self.unit = 'f'
        if value:
            if value.lower()[-1] in ('f', 'c'):
                self.unit = value.lower()[-1]
                value = value[:-1]
        return value

    def get_data(self):
        if self.parsed:
            temps = {'f': None, 'c': None}
            temps[self.unit] = self.parsed
            if temps['f'] is None:
                temps['f'] = ((temps['c'] / 5.0) * 9.0) + 32
            if temps['c'] is None:
                temps['c'] = ((temps['f'] - 32) * 5.0) / 9.0
            return {(self.key or self.param): temps}

    @classmethod
    def get_demo_config(cls):
        return {
            'type': 'range',
            'min': -50,
            'max': 140,
            'step': 0.1,
            'default': 80,
            'enabled': True,
        }


class InternalTemperature(BaseTemperature):
    param = 'i_temp'


class ExternalTemperature(BaseTemperature):
    param = 'e_temp'


class BaseHumidity(Metric):
    @classmethod
    def get_demo_config(cls):
        return {
            'type': 'range',
            'min': 0,
            'max': 1,
            'step': 0.001,
            'default': 0.45,
            'enabled': True,
        }

class InternalHumidity(BaseHumidity):
    param = 'i_hum'


class ExternalHumidity(BaseHumidity):
    param = 'e_hum'

class BasePressure(Metric):
    @classmethod
    def get_demo_config(cls):
        return {
            'type': 'range',
            'min': 20,
            'max': 40,
            'step': 0.1,
            'default': 29.61,
            'enabled': True,
        }

class InternalPressure(BasePressure):
    param = 'i_pres'


class ExternalPressure(BasePressure):
    param = 'e_pres'


class Wifi(Metric):
    param = 'wifi_dbm'

    def get_data(self):
        if self.parsed:
            if self.parsed >= -30:
                bars = 4
            elif self.parsed >= -67:
                bars = 3
            elif self.parsed >= -70:
                bars = 2
            elif self.parsed >= -80:
                bars = 1
            elif self.parsed >= -90:
                bars = 0
            else:
                bars = -1
            return {
                'wifi': {
                    'dbm': self.parsed,
                    'b': bars,
                }
            }

    @classmethod
    def get_demo_config(cls):
        return {
            'type': 'range',
            'min': -100,
            'max': 0,
            'step': 1,
            'default': -69,
            'enabled': True,
        }