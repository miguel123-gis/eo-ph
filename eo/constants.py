VALID_MODES = ['regular', 'annotate', 'export_all', 'cloudless']

FREQUENCY_MAP = {
    'monthly': 'ME',
    'quarterly': 'QE',
    'yearly': 'YE'
}

REQUIRED_PARAMETERS = [
    'start_date',
    'end_date',
    'latitude',
    'longitude',
    'buffer',
    'mode',
    'boundary',
    'to_zip'
]