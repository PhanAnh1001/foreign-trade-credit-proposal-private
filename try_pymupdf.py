"""Try to install and test pymupdf."""
import subprocess, sys
result = subprocess.run(
    [sys.executable, "-m", "pip", "install", "pymupdf", "-q"],
    capture_output=True, text=True
)
print(result.stdout or result.stderr or "OK")

try:
    import fitz
    print(f"pymupdf version: {fitz.version}")

    pdf_path = '/home/user/credit-proposal-private/data/uploads/mst/financial-statements/pdf/2024/MST_24CN_BCTC_KT_04042025040604.pdf'
    doc = fitz.open(pdf_path)
    print(f"Pages: {len(doc)}")

    page = doc[0]
    text = page.get_text()
    print(f"Text on page 1: {repr(text[:200]) if text else 'NONE'}")

    # Check if it has embedded images
    img_list = page.get_images()
    print(f"Images on page 1: {len(img_list)}")

except Exception as e:
    print(f"Error: {e}")
