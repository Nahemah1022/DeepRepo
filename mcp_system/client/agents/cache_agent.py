from agents.agent import Agent
from data_models.cache_agent_data_models import CacheAgentState
from preprocess.preprocess import Preprocess


class CacheAgentNodes:
    def __init__(self):
        pass

    def reasoning(self):
        pass




class CacheAgent(Agent):
    def __init__(self, preprocess:Preprocess):
        super.__init__(preprocess=preprocess, overall_state=CacheAgentState)
    

    
    def start(self):
        
        self.preprocess.get_data()
        