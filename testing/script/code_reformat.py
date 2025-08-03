def to_raw_string(s: str) -> str:
  """
  Converts a string with escape sequences (like '\n') into a 
  raw-style string representation (like '\\n').
  
  Args:
    s: The input string.
    
  Returns:
    The raw string representation.
  """
  # 1. Encode the string to bytes, turning escapes like '\n' into '\\n'
  encoded_bytes = s.encode('unicode_escape')
  
  # 2. Decode the bytes back to a string using a standard encoding
  raw_string = encoded_bytes.decode('utf-8')
  
  return raw_string


st = """class DBRole:
    WRITE = \"write\"
    READ = \"read\""""

print(to_raw_string(st))