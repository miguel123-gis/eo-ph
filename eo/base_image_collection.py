from dataclasses import dataclass

@dataclass(frozen=True)
class BaseImageCollection:
    start_date:str
    end_date:str
    lat:float
    lon:float
    collection:str