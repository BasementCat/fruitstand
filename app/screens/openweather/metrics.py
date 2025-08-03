from app.lib.metric import Metric

class BaseTemperature(Metric):
    format_description = '"<temp>;<units>", units is f/c/k or imperial/metric/standard'
    provides = {
        'temp': 'Temperature (float)',
        'units': 'Units (str, imperial/metric/standard)'
    }

    def parse(self, raw):
        if raw:
            try:
                parts = raw.split(';')
                if len(parts) == 2:
                    temp, units = parts
                else:
                    temp = parts
                    units = 'standard'
                temp = float(temp)
                units = {
                    'f': 'imperial',
                    'c': 'metric',
                    'k': 'standard',
                    'imperial': 'imperial',
                    'metric': 'metric',
                    'standard': 'standard',
                }[units.lower()]
                return {self.key: {
                    'temp': temp,
                    'units': units,
                }}
            except:
                pass

    @classmethod
    def get_demo_inputs(cls):
        return {
            'temp': {
                'label': "Temperature",
                'type': 'number',
                'default': 80,
            },
            'units': {
                'label': "Units",
                'type': 'select',
                'choices': {
                    'f': "Fahrenheit",
                    'c': "Celsius",
                    'k': "Kelvin",
                },
                'default': 'f',
            }
        }

    @classmethod
    def format_demo_inputs(cls, data):
        return ';'.join(map(str, [data['temp'], data['units']]))


class InternalTemperature(BaseTemperature):
    key = 'internal_temp'
    name = 'Internal Temp'
    description = 'Internal Temperature'
    param = 'i_temp'
    order = 10


class ExternalTemperature(BaseTemperature):
    key = 'external_temp'
    name = 'External Temp'
    description = 'External Temperature'
    param = 'e_temp'
    order = 20


class BaseHumidity(Metric):
    format_description = 'Humidity from 0.0-1.0 (percent)'
    provides = {
        None: 'Humidity (float)',
    }

    def parse(self, raw):
        if raw:
            try:
                return float(raw)
            except:
                pass

    @classmethod
    def get_demo_inputs(cls):
        return {
            'humidity': {
                'label': "Humidity",
                'type': 'range',
                'min': 0,
                'max': 100,
                'step': 1,
                'default': 35,
            },
        }

    @classmethod
    def format_demo_inputs(cls, data):
        return str(data['humidity'] / 100.0)


class InternalHumidity(BaseHumidity):
    key = 'internal_humidity'
    name = 'Internal Humidity'
    description = 'Internal Humidity'
    param = 'i_hum'
    order = 11


class ExternalHumidity(BaseHumidity):
    key = 'external_humidity'
    name = 'External Humidity'
    description = 'External Humidity'
    param = 'e_hum'
    order = 21


class BasePressure(Metric):
    format_description = '"<pressure>;<units>", units is inhg/mmhg/hpa or imperial/metric/standard'
    provides = {
        'pressure': 'Pressure (float)',
        'units': 'Units (str, imperial/metric/standard)'
    }

    def parse(self, raw):
        if raw:
            try:
                parts = raw.split(';')
                if len(parts) == 2:
                    pressure, units = parts
                else:
                    pressure = parts
                    units = 'standard'
                pressure = float(pressure)
                units = {
                    'inhg': 'imperial',
                    'mmhg': 'metric',
                    'hpa': 'standard',
                    'imperial': 'imperial',
                    'metric': 'metric',
                    'standard': 'standard',
                }[units.lower()]
                return {self.key: {
                    'pressure': pressure,
                    'units': units,
                }}
            except:
                pass

    @classmethod
    def get_demo_inputs(cls):
        return {
            'pressure': {
                'label': "Pressure",
                'type': 'number',
                'default': 29.61,
            },
            'units': {
                'label': "Units",
                'type': 'select',
                'choices': {
                    'inhg': "inHg",
                    'mmhg': "mmHg",
                    'hpa': "hPa",
                },
                'default': 'inhg',
            }
        }

    @classmethod
    def format_demo_inputs(cls, data):
        return ';'.join(map(str, [data['pressure'], data['units']]))


class InternalPressure(BasePressure):
    key = 'internal_pressure'
    name = 'Internal Pressure'
    description = 'Internal Pressure'
    param = 'i_pres'
    order = 12


class ExternalPressure(BasePressure):
    key = 'external_pressure'
    name = 'External Pressure'
    description = 'External Pressure'
    param = 'e_pres'
    order = 22
