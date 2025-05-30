# MCP System Client

## Setup

```
# in Client
uv sync
uv run test_repeat_client.py ../servers/lsp_mcp_server/.venv/bin/lsp-mcp-server -r <some-python-repo-root-path>


uv run deep_reader.py ../servers/lsp_mcp_server/.venv/bin/lsp-mcp-server -r <some-python-repo-root-path>
```

## Example Prompts

Prompt to use `FileReader` tool:
```
Use the `FileReader` tool to get the file content at host path `/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object.py` and summarize what it does.
```

Prompt to use `SymbolLocator` tool:
```
Use the `SymbolLocator` tool to get all locations and contexts of the keyword `url` at `/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/request_client.py`.
```

Answer:
```
I've found 13 occurrences of the keyword "url" in the specified file. Here's a summary of where and how it's being used:

1. In method signatures/parameters:
- `_retryable_session_request(self, method: str, url: str, headers: dict, **kwargs)` (line 181)
- `_request_with_manual_redirect(self, method: str, url: str, headers, **kwargs)` (line 254)
- `_session_request(self, method, url, headers, **kwargs)` (line 291)

2. In documentation:
- Parameter documentation describing "url (str): Target URL." (line 203)
- Parameter documentation describing "url (str): Initial AIS url." (line 268)

3. In code implementation:
- URL validation/checking: `if url.startswith(HTTPS)...` (line 211)
- URL construction: `url = f"{base}/{path.lstrip('/')}"` (line 241)
- Making HTTP requests:
  - `response = self._request_with_manual_redirect(method, url, headers, **kwargs)` (line 213)
  - `response = self._session_request(method, url, headers, **kwargs)` (line 216)
  - `self._retryable_session_request, method, url, headers, **kwargs` (line 250)
  - `self.session_manager.session.request(method, url, **proxy_request_kwargs)` (line 284)
  - `self.session_manager.session.request(method, url, **request_kwargs)` (line 295)

The keyword appears to be primarily used as a parameter for HTTP request methods and in the context of handling URL construction and request routing in this client implementation.
```

Prompt to use `DocumentSymbols` tool:
```
use the `DocumentSymbols` tool to get all Class symbols in the `/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object_reader.py` file
```

Answer:
```
I'll help you use the `DocumentSymbols` tool to get all Class symbols from the specified file. Since you want specifically Class symbols, I'll use the kind_filter parameter with the value 5 (which represents Class in the SymbolKind enum).
[Calling tool document_symbols with args {'file_path': '/Users/nahemah1022/NVIDIA/proj/aistore/python/aistore/sdk/obj/object_reader.py', 'kind_filter': 5}]
Looking at the results, there is one class defined in this file:

- `ObjectReader` (defined from line 16 to line 128)

The results also show all the methods and variables associated with this class, but since you specifically asked for Class symbols, the main relevant result is the ObjectReader class itself.
```

Prompt to use `HoverInformation` tool:
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


I want to see mcp_system/client/deep_reader.py connect_to_server function at ln 42 col 68 spaces 4. what does it do? And also the next mcp_system/client/deep_reader.py cleanup line 174 col 22. If you didn't get any respond from hovering tool, directly do the next mission
