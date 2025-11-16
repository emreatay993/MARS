"""
Generate PNG icons from the SVG source file.

This script converts the mars_logo.svg file into multiple PNG sizes
for use as application icons.
"""

from pathlib import Path

try:
    import cairosvg
    HAS_CAIROSVG = True
except ImportError:
    HAS_CAIROSVG = False
    print("Warning: cairosvg not found. Install with: pip install cairosvg")

def generate_icons():
    """Generate PNG icons from SVG in multiple sizes."""
    
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    svg_path = script_dir / "mars_logo.svg"
    
    if not svg_path.exists():
        print(f"Error: SVG file not found at {svg_path}")
        return False
    
    # Read SVG content
    svg_content = svg_path.read_text(encoding="utf-8")
    
    # Sizes to generate
    sizes = [16, 32, 64, 128, 256, 512]
    
    if not HAS_CAIROSVG:
        print("Cannot generate PNG files without cairosvg.")
        print("Please install it with: pip install cairosvg")
        return False
    
    # Generate PNGs
    outputs = {}
    for size in sizes:
        out_path = script_dir / f"mars_{size}.png"
        try:
            cairosvg.svg2png(
                bytestring=svg_content.encode("utf-8"),
                write_to=str(out_path),
                output_width=size,
                output_height=size
            )
            outputs[size] = str(out_path)
            print(f"Generated: {out_path.name}")
        except Exception as e:
            print(f"Error generating {size}x{size} icon: {e}")
    
    # Also create a .ico file for Windows (if pillow is available)
    try:
        from PIL import Image
        ico_path = script_dir / "mars_icon.ico"
        
        # Load the largest PNG
        img_256 = Image.open(script_dir / "mars_256.png")
        img_128 = Image.open(script_dir / "mars_128.png")
        img_64 = Image.open(script_dir / "mars_64.png")
        img_32 = Image.open(script_dir / "mars_32.png")
        img_16 = Image.open(script_dir / "mars_16.png")
        
        # Save as ICO with multiple sizes
        img_256.save(
            ico_path,
            format='ICO',
            sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
        )
        print(f"Generated: {ico_path.name}")
    except ImportError:
        print("PIL/Pillow not available, skipping .ico generation")
    except Exception as e:
        print(f"Error generating .ico file: {e}")
    
    print(f"\nSuccessfully generated {len(outputs)} PNG files.")
    return True

if __name__ == "__main__":
    generate_icons()

