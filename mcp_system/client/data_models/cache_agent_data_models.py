from dataclasses import dataclass
from typing import Optional, List, Dict, Tuple


@dataclass
class NodeInfo:
    type: str
    name: str
    path: str
    code_content: str

@dataclass
class CacheAgentState:
    node: NodeInfo
    dependencies:List[NodeInfo]
    context: Optional[str]