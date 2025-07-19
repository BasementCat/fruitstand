from flask import request


class Metric:
    _all_metrics = None

    param = None
    key = None
    datatype = float

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


class InternalTemperature(BaseTemperature):
    param = 'i_temp'


class ExternalTemperature(BaseTemperature):
    param = 'e_temp'


class BaseHumidity(Metric):
    pass

class InternalHumidity(BaseHumidity):
    param = 'i_hum'


class ExternalHumidity(BaseHumidity):
    param = 'e_hum'

class BasePressure(Metric):
    pass

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