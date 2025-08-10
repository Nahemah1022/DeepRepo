from preprocess.preprocess import Preprocess
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Type


class Agent(ABC):
    def __init__(self, preprocess:Preprocess, overall_state: Type):
        self.preprocess = preprocess
        self.overall_state = overall_state

    
    @abstractmethod
    def start(self):
        raise NotImplementedError("This method must be implemented by a subclass.")
    