# a framework for describing intents
from typing import TypedDict


class Intent(TypedDict):
    scenerio: str
    description: str
    abnormal: bool
    action: str
