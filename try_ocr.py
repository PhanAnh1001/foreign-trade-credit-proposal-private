"""Try OCR on the scanned PDF using pymupdf + PIL."""
import fitz
import io

try:
    from PIL import Image
    print("PIL available")
except ImportError:
    print("PIL not available - installing")
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "Pillow", "-q"])
    from PIL import Image

try:
    import pytesseract
    print("pytesseract available")
    HAS_TESSERACT = True
except ImportError:
    print("pytesseract not available")
    HAS_TESSERACT = False

pdf_path = '/home/user/credit-proposal-private/data/uploads/mst/financial-statements/pdf/2024/MST_24CN_BCTC_KT_04042025040604.pdf'
doc = fitz.open(pdf_path)
page = doc[5]  # Try page 6

# Get page as image (pixmap)
zoom = 2  # zoom factor for better resolution
mat = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=mat)
img_bytes = pix.tobytes("png")
img = Image.open(io.BytesIO(img_bytes))
print(f"Image size: {img.size}")

if HAS_TESSERACT:
    # Try OCR with Vietnamese support
    text = pytesseract.image_to_string(img, lang='vie')
    print("OCR result:", text[:500])
else:
    print("Cannot OCR without tesseract")
    print("Image saved to /tmp/test_page.png")
    img.save("/tmp/test_page.png")
