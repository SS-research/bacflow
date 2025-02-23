"""A compendium of Widmark coefficient estimation models"""


import enum
from abc import ABC, abstractmethod


class Sex(str, enum.Enum):
    M = "M"
    F = "F"


class abc_Widmark(ABC):
    """A base Widmark coefficient estimation model"""

    def __init__(self) -> None:
        self.mapping = {Sex.F: self.forward_F, Sex.M: self.forward_M}

    @abstractmethod
    def forward_F(self, **kwargs: float) -> float:
        pass

    @abstractmethod
    def forward_M(self, **kwargs: float) -> float:
        pass

    def __call__(self, sex: str, **kwargs: float) -> float:
        return self.mapping[Sex(sex)](**kwargs)


class Widmark(abc_Widmark):
    def forward_F(self, **kwargs: float) -> float:
        return 0.55

    def forward_M(self, **kwargs: float) -> float:
        return 0.68


class Watson(abc_Widmark):
    def forward_F(self, *, H: float, W: float, g: float, **kwargs: float) -> float:
        return 0.29218 + (12.666 * H - 2.4846) / W

    def forward_M(self, *, H: float, W: float, g: float, **kwargs: float) -> float:
        return 0.39834 + (12.725 * H - 0.11275 * g + 2.8993) / W


class Forrest(abc_Widmark):
    def forward_F(self, *, H: float, W: float, **kwargs: float) -> float:
        return 0.8736 - 0.0124 * W / H**2

    def forward_M(self, *, H: float, W: float, **kwargs: float) -> float:
        return 1.0178 - 0.012127 * W / H**2


class Seidl(abc_Widmark):
    def forward_F(self, *, H: float, W: float, **kwargs: float) -> float:
        return 0.31223 - 0.006446 * W + 0.4466 * H

    def forward_M(self, *, H: float, W: float, **kwargs: float) -> float:
        return 0.31608 - 0.004821 * W + 0.4632 * H


class Ulrich(abc_Widmark):
    def forward_F(self, *, H: float, W: float, **kwargs: float) -> float:
        raise ValueError("No estimator available")

    def forward_M(self, *, H: float, W: float, **kwargs: float) -> float:
        return 0.715 - 0.00462 * W + 0.22 * H


class Average(abc_Widmark):
    def forward_F(self, *, H: float, W: float, g: float, **kwargs: float) -> float:
        return (
            0.50766
            + 0.11165 * H
            - W * (0.001612 + 0.0031 / H**2)
            - (1 / W) * (0.62115 - 3.1665 * H)
        )

    def forward_M(self, *, H: float, W: float, g: float, **kwargs: float) -> float:
        return (
            0.62544
            + 0.13664 * H
            - W * (0.00189 + 0.002425 / H**2)
            + (1 / W) * (0.57986 + 2.545 * H - 0.02255 * g)
        )


def test_widmark_models():
    widmark = Widmark()
    watson = Watson()
    forrest = Forrest()
    seidl = Seidl()
    ulrich = Ulrich()
    average = Average()

    H = 170.0  # Replace with actual values
    W = 70.0  # Replace with actual values
    g = 18.0  # Replace with actual values

    print("Widmark (F):", widmark(sex=Sex.F, H=H, W=W, g=g))
    print("Widmark (M):", widmark(sex=Sex.M, H=H, W=W, g=g))

    print("Watson (F):", watson(sex=Sex.F, H=H, W=W, g=g))
    print("Watson (M):", watson(sex=Sex.M, H=H, W=W, g=g))

    print("Forrest (F):", forrest(sex=Sex.F, H=H, W=W))
    print("Forrest (M):", forrest(sex=Sex.M, H=H, W=W))

    print("Seidl (F):", seidl(sex=Sex.F, H=H, W=W))
    print("Seidl (M):", seidl(sex=Sex.M, H=H, W=W))

    try:
        print("Ulrich (F):", ulrich(sex=Sex.F, H=H, W=W))
    except ValueError as e:
        print("Ulrich (F):", e)

    print("Ulrich (M):", ulrich(sex=Sex.M, H=H, W=W))

    print("Average (F):", average(sex=Sex.F, H=H, W=W, g=g))
    print("Average (M):", average(sex=Sex.M, H=H, W=W, g=g))


if __name__ == "__main__":
    test_widmark_models()
