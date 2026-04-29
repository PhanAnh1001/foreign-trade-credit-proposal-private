"""Install project dependencies programmatically."""
import subprocess
import sys

packages = [
    "langgraph>=0.2.0",
    "langchain>=0.3.0",
    "langchain-groq>=0.2.0",
    "langchain-community>=0.3.0",
    "groq>=0.11.0",
    "pydantic>=2.0.0",
    "pdfplumber>=0.11.0",
    "python-docx>=1.1.0",
    "tavily-python>=0.5.0",
    "python-dotenv>=1.0.0",
]

for pkg in packages:
    print(f"Installing {pkg}...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg, "-q"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr}")
    else:
        print(f"  OK")

# Install markitdown from PyPI
print("Installing markitdown from PyPI...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "markitdown", "-q"],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"  ERROR: {result.stderr}")
else:
    print(f"  OK")

print("Done!")
