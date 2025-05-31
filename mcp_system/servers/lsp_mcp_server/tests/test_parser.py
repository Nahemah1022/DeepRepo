import unittest
from lsp_mcp_server.parser import parse

class TestServer(unittest.TestCase):
    def test_parse(self):
        result = parse()
