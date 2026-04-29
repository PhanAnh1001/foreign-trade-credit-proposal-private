"""Fix cryptography package conflict and install pypdf as alternative."""
import subprocess
import sys

# Upgrade cryptography to override system version
print("Upgrading cryptography...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "--upgrade", "cryptography", "-q"],
    capture_output=True, text=True
)
print(result.stdout or result.stderr or "OK")

# Install pypdf as alternative PDF parser (doesn't need cryptography for basic use)
print("Installing pypdf...")
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "pypdf", "-q"],
    capture_output=True, text=True
)
print(result.stdout or result.stderr or "OK")

# Test
print("\nTesting imports...")
try:
    import pdfplumber
    print("pdfplumber: OK")
except Exception as e:
    print(f"pdfplumber: FAIL - {e}")

try:
    import pypdf
    print("pypdf: OK")
except Exception as e:
    print(f"pypdf: FAIL - {e}")
