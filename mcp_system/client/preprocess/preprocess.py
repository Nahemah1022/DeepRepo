from abc import ABC, abstractmethod
class Preprocess:
    @abstractmethod
    def get_data(self):
        raise NotImplementedError("This method must be implemented by a subclass.")
    
    
    @abstractmethod
    def get_graph(self):
        raise NotImplementedError("This method must be implemented by a subclass.")
    

    @abstractmethod
    def store_data(self):
        print("Done nothing")