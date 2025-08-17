from preprocess.cache_agent_preprocess import CacheAgentPreprocess
from agents.cache_agent import CacheAgent
from dotenv import load_dotenv
load_dotenv()
tp = CacheAgentPreprocess(file_path="/Users/bytedance/Bowen_Yang_SWE/PRIVATE_WORKS/DeepRepo/testing/testing_graph/sample_1_db_client/rule_1.json")


agent = CacheAgent(preprocess=tp)
agent.start()



