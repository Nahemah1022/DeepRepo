# MCP System Client

## Setup

```
uv sync
uv run test_repeat_client.py ../servers/lsp_mcp_server/.venv/bin/lsp-mcp-server -r <some-python-repo-root-path>
```

## Example Prompts

Prompt:
```
Use the `HoverInformation` tool to get information of the Object class at file path `<some-python-repo-root-path>/<file-path-of-your-interest>`. line_num is 64, and character_num is 9. Figure out the keyword to use by yourself
```

Answer:
```
Based on the given information, I'll use the `HoverInformation` tool to get information about the Object class. Since you're asking about the Object class and provided a file path that contains "object.py", I'll use "Object" as the keyword.
[Calling tool hover_information with args {'file_path': '/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py', 'line_num': 64, 'character_num': 9, 'keyword': 'Object'}]
The hover information shows that `Object` is a class that handles interactions with objects in AIS (AIStore). It requires:
1. A RequestClient for HTTP requests
2. BucketDetails for bucket metadata
3. A name string for the object
4. Optional ObjectProps for object properties

The class is designed to provide methods for working with objects within the AIStore system.
```
