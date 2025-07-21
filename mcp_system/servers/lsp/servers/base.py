import subprocess
import threading
import json
import time
import select
from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Union, Any, Set, Tuple, Optional

from lsprotocol import types, converters

class LangServer(ABC):
    def __init__(self, cmd, root_uri: str):
        self.cmd = cmd
        self.proc = subprocess.Popen(
            self.cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,  # Use binary mode for consistent encoding
            bufsize=0,
        )
        threading.Thread(target=self._read_stderr, daemon=True).start()

        self._id = 0
        self.converter = converters.get_converter()
        self.root_uri = Path(root_uri).resolve().as_uri() if not root_uri.startswith("file://") else root_uri

        # Initialize the language server
        self.request(
            types.InitializeRequest,
            params=types.InitializeParams(
                process_id=None,
                root_uri=root_uri,
                capabilities=types.ClientCapabilities(
                    text_document=types.TextDocumentClientCapabilities(
                        # Explicitly disable diagnostics by setting publish_diagnostics to None
                        publish_diagnostics=None
                    )
                ),
                workspace_folders=[
                    types.WorkspaceFolder(uri=root_uri, name=Path(root_uri).name)
                ],
            )
        )
        self.notify(types.InitializedNotification(params=types.InitializedParams()))
        
        # Try to disable diagnostics by sending a configuration change
        try:
            self.notify(types.WorkspaceDidChangeConfigurationNotification(
                params=types.DidChangeConfigurationParams(
                    settings={
                        "python": {
                            "analysis": {
                                "diagnosticMode": "off",
                                "autoImportCompletions": False,
                                "typeCheckingMode": "off"
                            }
                        },
                        "pyright": {
                            "disableLanguageService": True
                        }
                    }
                )
            ))
        except Exception as e:
            # If this fails, it's not critical - we'll just filter the messages
            print(f"Note: Could not disable diagnostics: {e}")

    def _read_stderr(self):
        """Read stderr output from the language server process"""
        if self.proc and self.proc.stderr:
            for line in self.proc.stderr:
                print("[stderr]", line.strip())

    def _send(self, msg):
        """Send a message to the language server via stdio"""
        if not self.proc or not self.proc.stdin:
            raise RuntimeError("LSP process not started or stdin not available.")
        
        payload = self.converter.unstructure(msg)
        body = json.dumps(payload)
        
        # LSP over stdio uses Content-Length header followed by the JSON payload
        header = f"Content-Length: {len(body)}\r\n\r\n"
        message = header + body
        
        try:
            self.proc.stdin.write(message.encode('utf-8'))
            self.proc.stdin.flush()
        except (IOError, OSError) as e:
            raise RuntimeError(f"Failed to send message to LSP server: {e}")

    def _read_message(self) -> Optional[dict]:
        """Read a complete message from the language server with proper LSP framing"""
        if not self.proc or not self.proc.stdout:
            return None
        
        try:
            # Read headers - stop at the first empty line
            headers = {}
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    return None
                line = line.rstrip(b'\r\n')
                if line == b'':
                    break
                if b':' in line:
                    k, v = line.split(b':', 1)
                    headers[k.strip().decode('utf-8')] = v.strip().decode('utf-8')
            
            # Read body with exact content length
            content_length = int(headers.get("Content-Length", 0))
            if content_length == 0:
                return None
            
            # Read exactly the specified number of bytes
            body = self.proc.stdout.read(content_length)
            if len(body) != content_length:
                print(f"Warning: Expected {content_length} bytes but got {len(body)}, body: {body}")
                return None
            
            # Parse JSON - this should now be a complete, valid JSON object
            return json.loads(body.decode('utf-8'))
        except (json.JSONDecodeError, ValueError, IOError, OSError) as e:
            print(f"Error reading message from LSP server: {e}")
            return None

    def _wait_for(self, target_id, timeout=5.0):
        """Wait for a specific response from the language server with improved timeout"""
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                # Use select to check if data is available
                if not self.proc or not self.proc.stdout:
                    break
                ready, _, _ = select.select([self.proc.stdout], [], [], 0.1)
                if not ready:
                    continue
                
                message = self._read_message()
                if not message:
                    continue
                
                # Skip all diagnostic-related notifications
                method = message.get("method", "")
                if method in [
                    "textDocument/publishDiagnostics",
                    "textDocument/publishDiagnostics/relatedInformation",
                    "textDocument/publishDiagnostics/tagSupport"
                ]:
                    # print(f"Skipping diagnostic message: {method}")
                    continue
                
                # Return the message if it matches our target ID
                if message.get("id") == target_id:
                    return message
            except (IOError, OSError) as e:
                print(f"Error waiting for LSP response: {e}")
                break
        
        return None

    def request(self, cls: types.REQUESTS, params) -> types.RESPONSES:
        """Send a request to the language server and wait for response"""
        self._id += 1
        msg = cls(params=params, id=self._id)
        self._send(msg)
        return self._wait_for(self._id)

    def notify(self, msg: types.NOTIFICATIONS):
        """Send a notification to the language server"""
        return self._send(msg)

    def close(self):
        """Close the connection and terminate the language server"""
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
            self.proc = None

    def __del__(self):
        """Cleanup when the object is destroyed"""
        self.close()

    def _open(self, uri: str):
        self.notify(types.TextDocumentDidOpenNotification(
            params=types.DidOpenTextDocumentParams(
                text_document=types.TextDocumentItem(
                    uri=uri,
                    language_id=self.language_id,
                    version=1,
                    text=self._read_file_from_uri(uri)
                )
            )
        ))

    def _read_file_from_uri(self, uri: str) -> str:
        parsed = urlparse(uri)
        file_path = Path(unquote(parsed.path))
        return file_path.read_text(encoding="utf-8")

    def show_definition(self, line: int, character: int, keyword: str, path: str):
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
        uri = Path(path).resolve().as_uri() if not path.startswith("file://") else path
        self._open(uri)
        result = self.request(
            types.TextDocumentDefinitionRequest,
            params=types.DefinitionParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=self.locator(line, character, keyword, path),
            )
        )
        if result is None:
            return None
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
        uri = Path(path).resolve().as_uri() if not path.startswith("file://") else path
        self._open(uri)

        result = self.request(
            types.TextDocumentHoverRequest,
            params=types.HoverParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=self.locator(line, character, keyword, path),
            )
        )
        return self.converter.structure(result["result"], types.Hover).contents.value

    def references(self, line: int, character: int, keyword: str, path: str) -> list[types.Location]:
        """
        Retrieves all references (including definition) to the given symbol in the codebase.

        This includes variable usages, function calls, and class references depending on context.

        Args:
            line: Approximate line number where the keyword appears.
            character: Approximate character offset on the line.
            keyword: The target symbol to retrieve references for.
            path: Path to the source file (with or without 'file://' prefix).

        Returns:
            A list of `types.Location` where the symbol is referenced.
        """
        uri = Path(path).resolve().as_uri() if not path.startswith("file://") else path
        self._open(uri)

        position = self.locator(line, character, keyword, path)
        result = self.request(
            types.TextDocumentReferencesRequest,
            params=types.ReferenceParams(
                text_document=types.TextDocumentIdentifier(uri=uri),
                position=position,
                context=types.ReferenceContext(include_declaration=True)
            )
        )
        return self.converter.structure(result["result"], list[types.Location])

    def document_symbols(
        self,
        path: str,
        kind_filter: Union[types.SymbolKind, list[types.SymbolKind], None] = None
    ) -> Union[list[types.DocumentSymbol], list[types.SymbolInformation]]:
        """
        Retrieves symbols defined in the given file, optionally filtering by symbol kind(s).

        Args:
            path: Path to the source file.
            kind_filter: Optional single or list of SymbolKind values to include (e.g., Function, Variable).

        Returns:
            A filtered list of DocumentSymbol or SymbolInformation.
        """
        uri = Path(path).resolve().as_uri() if not path.startswith("file://") else path
        self._open(uri)

        result = self.request(
            types.TextDocumentDocumentSymbolRequest,
            params=types.DocumentSymbolParams(
                text_document=types.TextDocumentIdentifier(uri=uri)
            )
        )

        raw = result.get("result", [])

        if not raw:
            return []

        # Normalize kind_filter to a set of SymbolKinds
        if kind_filter is not None:
            if isinstance(kind_filter, types.SymbolKind):
                kind_filter = {kind_filter}
            else:
                kind_filter = set(kind_filter)

        def filter_by_kind(symbols: list[Any]) -> list[Any]:
            def match(s): return kind_filter is None or s.kind in kind_filter
            return [s for s in symbols if match(s)]

        if "range" in raw[0]:  # DocumentSymbol
            structured = self.converter.structure(raw, list[types.DocumentSymbol])
            return filter_by_kind(structured)
        else:  # SymbolInformation
            structured = self.converter.structure(raw, list[types.SymbolInformation])
            return filter_by_kind(structured)

    @property
    @abstractmethod
    def language_id(self) -> str:
        """LSP language ID, e.g., 'python', 'cpp', etc."""
        pass

    @property
    @abstractmethod
    def separators(self) -> Set[str]:
        pass

    @property
    @abstractmethod
    def keywords(self) -> Set[str]:
        # Define any string keywords you want to exclude from scanning
        pass

    @property
    @abstractmethod
    def inlie_comment(self) -> str:
        pass

    @property
    @abstractmethod
    def multiline_comment(self) -> Tuple[str, str]:
        pass

    @property
    @abstractmethod
    def string_delimiters(self) -> list[Tuple[str, str]]:
        """Return the string delimiters for the language, e.g., [('"', '"'), ("'", "'")] for Python."""
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
