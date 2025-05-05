| Request                             | Purpose                                                         |
| ----------------------------------- | --------------------------------------------------------------- |
| `TextDocumentDefinitionRequest`     | Jump to definition of a symbol (you already use this)           |
| `TextDocumentHoverRequest`          | Show type info / docstring on hover (you already use this)      |
| `TextDocumentReferencesRequest`     | Show all references to a symbol                                 |
| `TextDocumentImplementationRequest` | Go to implementation (useful for interfaces/abstracts)          |
| `TextDocumentTypeDefinitionRequest` | Go to the type (esp. for type aliases / inferred types)         |
| `TextDocumentDocumentSymbolRequest` | Retrieve top-level symbols (e.g., functions, classes) in a file |
| `WorkspaceSymbolRequest`            | Search for symbols across the entire workspace                  |

| Request                                   | Purpose                                  |
| ----------------------------------------- | ---------------------------------------- |
| `TextDocumentPrepareCallHierarchyRequest` | Start point for call hierarchy traversal |
| `CallHierarchyIncomingCallsRequest`       | Who calls this function                  |
| `CallHierarchyOutgoingCallsRequest`       | What functions this function calls       |
| `TypeHierarchySupertypesRequest`          | Get the base class(es)                   |
| `TypeHierarchySubtypesRequest`            | Get the derived class(es)                |

| Request                                  | Purpose                                                                                              |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `TextDocumentDocumentHighlightRequest`   | Highlights symbol usages in current doc (local context)                                              |
| `TextDocumentMonikerRequest`             | Language-agnostic way to track symbol identity (for cross-repo or module resolution)                 |
| `TextDocumentSemanticTokensRangeRequest` | Token classifications (e.g., variable, class, function) — can help your agent understand token roles |
| `TextDocumentSelectionRangeRequest`      | Hierarchical selection context — e.g., expand from variable → statement → function                   |
| `WorkspaceWorkspaceFoldersRequest`       | Get folder structure — useful to build project-level symbol maps                                     |
