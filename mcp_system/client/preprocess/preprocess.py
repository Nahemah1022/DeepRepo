from abc import ABC, abstractmethod
class Preprocess:
    @abstractmethod
    def get_data(self):
        raise NotImplementedError("This method must be implemented by a subclass.")
