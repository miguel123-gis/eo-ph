from dataclasses import dataclass, fields, asdict
from eo.constants import REQUIRED_PARAMETERS, FREQUENCY_MAP

@dataclass(frozen=True)
class Payload:
    start_date: str
    end_date: str
    latitude: float
    longitude: float
    buffer: float
    frequency: str
    annotate: bool
    boundary: bool
    export_all: bool
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

def validate_payload(data):
    if data.get('frequency') and data.get('frequency') not in FREQUENCY_MAP.keys():
        raise InvalidFrequencyError(message='Invalid frequency')
    
    for key in data:
        if key not in required_parameters:
            raise InvalidPayloadError(message='Invalid payload: missing key')
        
        if data.get(key) == '':
            raise InvalidPayloadError(message='Invalid payload: blank value/s')
        
    return asdict(Payload(
        start_date = data.get('start_date'),
        end_date = data.get('end_date'),
        latitude = data.get('latitude'),
        longitude = data.get('longitude'),
        buffer = data.get('buffer'),
        frequency = data.get('frequency', False),
        annotate = data.get('annotate', False),
        boundary = data.get('boundary', False),
        export_all = data.get('all', False),
        to_zip = data.get('to_zip', True)
    ))