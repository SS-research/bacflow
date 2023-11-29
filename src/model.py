"""A compendium of blood alcohol concentration (BAC) estimation models

All BAC estimation models belong to the intrunsive Widmark family.
"""
from abc import ABC, abstractmethod
from typing import Any


class abc_Model(ABC):
    """A base BAC estimation model from self-reported drinking history"""

    def __init__(self, bodyfactor: str = "", *args: Any, **kwargs: Any) -> None:
        ...

    def _distribution(self):
        ...

    def _elimination(self):
        ...

    def _absorption(self):
        ...

    def predict(self):
        ...

    def __call__(self, history: Any) -> Any:
        ...
