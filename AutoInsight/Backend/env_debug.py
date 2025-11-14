from dotenv import dotenv_values
import os

print("=== dotenv_values() ===")
print(dotenv_values(".env"))

print("\n=== os.getenv() ===")
print(os.getenv("GOOGLE_API_KEY"))

