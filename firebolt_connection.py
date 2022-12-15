import os
from firebolt.client.auth import UsernamePassword
from firebolt.db import connect

def get_firebolt_connection():
  engine_name = os.getenv("FIREBOLT_ENGINE")
  database_name = os.getenv("FIREBOLT_DATABASE")
  username = os.getenv("FIREBOLT_USER")
  password = os.getenv("FIREBOLT_PASSWORD")

  # create a connection based on provided credentials
  connection = connect(
    auth=UsernamePassword(username, password),
    engine_name=engine_name,
    database=database_name,
  )
  return connection
