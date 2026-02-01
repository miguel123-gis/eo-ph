from dataclasses import dataclass, fields, asdict
from eo.constants import VALID_MODES, FREQUENCY_MAP

@dataclass(frozen=True)
class Payload:
    latitude: float
    longitude: float
    start_date: str
    end_date: str
    buffer: float
    frequency: str | bool
    # Modes
    mode: str 
    # Sub-mode for annotate
    boundary: bool
    # Always True
    to_zip: bool = True

required_parameters = [field.name for field in fields(Payload)]

class InvalidPayloadError(Exception): 
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message
    
class InvalidFrequencyError(Exception): 
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

class InvalidModeError(Exception): 
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message

def validate_payload(data):
    if data.get('frequency') == '':
        data['frequency'] = False
    elif data.get('frequency') not in FREQUENCY_MAP.keys():
        raise InvalidFrequencyError(message='Invalid frequency')

    mode = data.get('mode')
    if data.get('mode') not in VALID_MODES:
        raise InvalidModeError(message='Invalid mode')
    
    for key in data:
        if key not in required_parameters:
            raise InvalidPayloadError(message='Invalid payload: missing key')
        
        if data.get(key) == '':
            raise InvalidPayloadError(message='Invalid payload: blank value/s')
        
    _on_as_bool = lambda value: True if value == 'on' else value
        
    return asdict(Payload(
        start_date = data.get('start_date'),
        end_date = data.get('end_date'),
        latitude = data.get('latitude'),
        longitude = data.get('longitude'),
        buffer = data.get('buffer'),
        frequency = data.get('frequency', False),
        mode = data.get('mode'),
        boundary = _on_as_bool(data.get('boundary', False)),
        to_zip = data.get('to_zip', True),
    ))