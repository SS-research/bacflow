import typing
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Drink:
    name: str
    vol: float
    alc_prop: float
    time: datetime
    sip_interval: int
    alc_kg: float = field(init=False)

    def __post_init__(self):
        alc_vol = self.vol * self.alc_prop
        self.alc_kg = alc_vol * 0.789

    def split_into_sips(self) -> list[typing.Self]:
        if self.sip_interval == 1:
            return [self]

        sips = []
        sip_volume = self.vol / self.sip_interval
        for i in range(self.sip_interval):
            sip_time = self.time + timedelta(minutes=i)
            sips.append(Drink(
                name=self.name,
                vol=sip_volume,
                alc_prop=self.alc_prop,
                time=sip_time,
                sip_interval=1
            ))

        return sips
