import os
import shutil

print("\n=== PATH ENVIRONMENT ===")
for path in os.environ["PATH"].split(";"):
    print(path)

print("\n=== CHECKING TOOL AVAILABILITY ===")

# Check Tesseract
tesseract_path = shutil.which("tesseract")
if tesseract_path:
    print(f"Tesseract FOUND at: {tesseract_path}")
else:
    print("Tesseract NOT found in PATH")

# Check Poppler's pdftoppm
pdftoppm_path = shutil.which("pdftoppm")
if pdftoppm_path:
    print(f"pdftoppm FOUND at: {pdftoppm_path}")
else:
    print("pdftoppm NOT found in PATH")

# Show current Python executable and environment
print("\n=== PYTHON ENVIRONMENT ===")
print(f"Python executable: {os.sys.executable}")
print(f"Working directory: {os.getcwd()}")
