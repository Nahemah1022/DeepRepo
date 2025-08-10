from preprocess. cache_agent_preprocess import CacheAgentPreprocess

tp = CacheAgentPreprocess(file_path="/Users/bytedance/Bowen_Yang_SWE/PRIVATE_WORKS/DeepRepo/testing/testing_graph/sample_1_db_client/rule_1.json")
tp.loadgraph()
print(tp.graph[-1])

