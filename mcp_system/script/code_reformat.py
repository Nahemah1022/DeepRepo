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


st = """def create_db_handle(connect_string):
    logging.info("using bytedmysql")
    from bytedmysql import sqlalchemy_init
    sqlalchemy_init()
    engine = create_engine(connect_string, pool_recycle=180)
    base_cls = automap_base()
    base_cls.prepare(engine, reflect=True)
    return DBHandle(engine, base_cls)"""

print(to_raw_string(st))