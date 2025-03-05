import typing
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum


class FoodIntakeCategory(str, Enum):
    light = "light"  # small amount of food, typically consumed to curb hunger between meals, such as a piece of fruit, a handful of nuts, or a small yogurt.
    moderate = "moderate"  # sufficient amount of food to satisfy hunger, usually a regular meal, such as a sandwich, a bowl of salad, or a standard portion of pasta.
    heavy = "heavy"  # large amount of food, often consumed for special occasions or when very hungry, such as a multi-course meal with several dishes, or a buffet.

    def __str__(self) -> str:
        return self.value


class DriverProfile(str, Enum):
    regular = "regular"
    novice = "novice"
    professional = "professional"

    def __str__(self) -> str:
        return self.value


class Model(str, Enum):
    average = "average"
    Forrest = "Forrest"
    Seidl = "Seidl"
    Ulrich = "Ulrich"
    Watson = "Watson"
    Widmark = "Widmark"

    def __str__(self) -> str:
        return self.value


class Sex(str, Enum):
    F = "F"
    M = "M"

    def __str__(self) -> str:
        return self.value


@dataclass
class Person:
    DoB: date
    height: float 
    weight: float 
    sex: Sex

    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.DoB.year - ((today.month, today.day) < (self.DoB.month, self.DoB.day))


@dataclass
class FoodIntake:
    time: datetime
    category: FoodIntakeCategory


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
