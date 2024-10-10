from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Drink:
    name: str
    vol: float
    alc_prop: float
    time: datetime
    alc_vol: float = field(init=False)
    alc_kg: float = field(init=False)

    def __post_init__(self):
        self.alc_vol = self.vol * self.alc_prop
        self.alc_kg = self.alc_vol * 0.789
