from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import io
import os

def create_watermark(text, page_width, page_height, rotation_angle):
    """Create watermark with specific rotation angle"""
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_width, page_height))
    
    can.setFont("Helvetica-Bold", 50)
    can.setFillColor(colors.grey, alpha=0.2)
    can.saveState()
    
    # Position at center
    can.translate(page_width/2, page_height/2)
    can.rotate(rotation_angle)
    can.drawCentredString(0, 0, text)
    can.restoreState()
    
    can.save()
    packet.seek(0)
    return PdfReader(packet)

def add_watermark_to_pdf(input_pdf, output_pdf, watermark_text="Alberto Diaz-Durana"):
    """Add watermark to all pages of PDF"""
    try:
        reader = PdfReader(input_pdf)
        writer = PdfWriter()
        
        total_pages = len(reader.pages)
        
        for page_num, page in enumerate(reader.pages, 1):
            page_width = float(page.mediabox.width)
            page_height = float(page.mediabox.height)
            
            # Get page rotation metadata
            page_rotation = int(page.get("/Rotate", 0))
            
            # Detect if page is landscape (width > height)
            is_landscape = page_width > page_height
            
            # Determine watermark angle
            if page_rotation == 270:
                # 270° rotated pages need positive 45° angle
                watermark_angle = 45
            elif page_rotation == 90:
                # 90° rotated pages need negative 45° angle  
                watermark_angle = -45
            elif page_rotation == 180:
                # 180° rotated pages need negative 135° angle
                watermark_angle = -135
            elif page_rotation == 0:
                # No rotation: use orientation detection
                if is_landscape:
                    watermark_angle = -45  # Landscape: negative angle
                else:
                    watermark_angle = 45   # Portrait: positive angle
            else:
                watermark_angle = 45  # Default
            
            # Debug info
            orientation = "Landscape" if is_landscape else "Portrait"
            rot_info = f", Rotation: {page_rotation}°" if page_rotation != 0 else ""
            print(f"  Page {page_num}: {orientation} ({page_width:.0f}x{page_height:.0f}){rot_info} → Watermark angle: {watermark_angle}°")
            
            # Create watermark
            watermark = create_watermark(watermark_text, page_width, page_height, watermark_angle)
            page.merge_page(watermark.pages[0])
            writer.add_page(page)
        
        with open(output_pdf, 'wb') as f:
            writer.write(f)
        
        return True, total_pages
    except Exception as e:
        print(f"  Error: {e}")
        return False, 0


# ===== AUTOMATICALLY FIND FILES TO WATERMARK =====
# Process all PDFs in original/ that don't exist in watermarked/
original_dir = "./original"
output_dir = "./watermarked"
os.makedirs(output_dir, exist_ok=True)

original_files = set(f for f in os.listdir(original_dir) if f.endswith(".pdf"))
watermarked_files = set(f for f in os.listdir(output_dir) if f.endswith(".pdf"))
files_to_watermark = [os.path.join(original_dir, f) for f in original_files - watermarked_files]

print("="*70)
print(f"Watermarking {len(files_to_watermark)} selected file(s)")
print("="*70)
print()

processed = 0
skipped = 0

for filepath in files_to_watermark:
    if os.path.exists(filepath):
        print(f"Processing: {filepath}")
        filename = os.path.basename(filepath)
        output_path = os.path.join(output_dir, filename)
        success, pages = add_watermark_to_pdf(filepath, output_path)
        if success:
            print(f"  ✓ Success ({pages} page(s))\n")
            processed += 1
        else:
            print(f"  ✗ Failed\n")
            skipped += 1
    else:
        print(f"✗ Not found: {filepath}\n")
        skipped += 1

print("="*70)
print(f"✓ Successfully processed: {processed}")
print(f"✗ Skipped/Failed: {skipped}")
print(f"\nWatermarked files saved to: {output_dir}")
print("="*70)