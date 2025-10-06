from dataclasses import dataclass

@dataclass
class TimeSpan:
    start: float
    duration: float

@dataclass
class Word:
    time: TimeSpan
    baseFreq:float
    wordStr:str