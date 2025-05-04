import subprocess
import threading
import json
import time
import select

from lsprotocol import types, converters
from abc import ABC, abstractmethod

class LangServer(ABC):
    def __init__(self, cmd, root_uri: str):
        self.cmd = cmd
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,
        )
        threading.Thread(target=self._read_stderr, daemon=True).start()

        self._id = 0
        self.converter = converters.get_converter()
        root_uri = root_uri if root_uri.startswith("file://") else f"file://{root_uri}"

        self._send("initialize", {
            "processId": None,
            "root_uri": f"file://{root_uri}",
            "capabilities": {},
        }, id=self._id)
        self._wait_for(self._id)

        self._send("initialized", {})

    def _read_stderr(self):
        for line in self.proc.stderr:
            print("[stderr]", line.strip())

    def _send(self, method, params, id=None):
        if not self.proc:
            raise RuntimeError("LSP process not started.")
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        if id is not None:
            payload["id"] = id
        body = json.dumps(payload)
        header = f"Content-Length: {len(body)}\r\n\r\n"
        self.proc.stdin.write(header + body)
        self.proc.stdin.flush()

    def _wait_for(self, target_id, timeout=3.0):
        start = time.time()
        if not self.proc:
            raise RuntimeError("LSP process not started.")

        while time.time() - start < timeout:
            ready, _, _ = select.select([self.proc.stdout], [], [], 0.1)
            if not ready:
                continue
            headers = {}
            while True:
                line = self.proc.stdout.readline()
                if line in ('\r\n', '\n', ''):
                    break
                if ":" in line:
                    k, v = line.split(":", 1)
                    headers[k.strip()] = v.strip()
            content_length = int(headers.get("Content-Length", 0))
            if content_length == 0:
                continue
            body = self.proc.stdout.read(content_length)
            message = json.loads(body)
            if message.get("id") == target_id:
                return message
        return None

    def request(self, method, params):
        self._id += 1
        self._send(method, params, id=self._id)
        return self._wait_for(self._id)

    def _open(self, uri: str):
        self._send("textDocument/didOpen", {
            "textDocument": {
                "uri": uri,
                "languageId": self.language_id,
                "version": 1,
            }
        })

    def show_definition(self, line: int, character: int, keyword: str, path: str) -> types.Location:
        """
        Finds the definition of the given keyword in the specified file by querying the LSP server.

        Uses the implemented `locator` method to refine the AI-provided approximate (line, character)
        into an exact position of the keyword, then sends a `textDocument/definition` request to
        retrieve the symbol definition location.

        Args:
            line: Approximate line number where the keyword appears.
            character: Approximate character offset on the line.
            keyword: The target symbol to locate the definition for.
            path: Path to the source file (with or without 'file://' prefix).

        Returns:
            A `types.Location` object representing the definition location.
        """
        uri = path if path.startswith("file://") else f"file://{path}"
        self._open(uri)

        position = self.locator(line, character, keyword, path)
        result = self.request("textDocument/definition", {
            "textDocument": {"uri": uri},
            "position": self.converter.unstructure(position, unstructure_as=types.Position),
        })

        return self.converter.structure(result, types.TextDocumentTypeDefinitionResponse).result

    def hover(self, line: int, character: int, keyword: str, path: str) -> types.Hover:
        """
        Retrieves hover information (e.g., type or documentation) for the given keyword
        in the specified file by querying the LSP server.

        Uses the implemented `locator` method to refine the AI-provided approximate (line, character)
        into the exact position of the keyword, then sends a `textDocument/hover` request
        to obtain reference information for that symbol.

        Args:
            line: Approximate line number where the keyword appears.
            character: Approximate character offset on the line.
            keyword: The target symbol to retrieve hover info for.
            path: Path to the source file (with or without 'file://' prefix).

        Returns:
            A `types.Hover` object containing reference/documentation information.
        """
        uri = path if path.startswith("file://") else f"file://{path}"
        self._open(uri)

        position = self.locator(line, character, keyword, path)
        result = self.request("textDocument/hover", {
            "textDocument": {"uri": uri},
            "position": self.converter.unstructure(position, unstructure_as=types.Position),
        })

        return self.converter.structure(result["result"], types.Hover).contents.value

    @property
    @abstractmethod
    def language_id(self) -> str:
        pass

    @abstractmethod
    def locator(self, line: int, character: int, keyword: str, path: str) -> types.Position:
        """
        Refines an approximate (line, character) position provided by an AI model
        by locating the exact position of the given keyword in the source code.

        This method is intended to improve precision when the AI cannot accurately
        pinpoint the exact location, enabling reliable downstream usage.
        """
        pass
