# MARS Application Icons

This directory contains the application icons for MARS (Modal Analysis Response Solver).

## Files

- **mars_logo.svg** - Source SVG icon (512x512)
- **mars_icon.ico** - Multi-resolution Windows icon file
- **mars_16.png** - 16x16 PNG icon
- **mars_32.png** - 32x32 PNG icon
- **mars_64.png** - 64x64 PNG icon
- **mars_128.png** - 128x128 PNG icon
- **mars_256.png** - 256x256 PNG icon
- **mars_512.png** - 512x512 PNG icon
- **generate_icons.py** - Script to regenerate PNG/ICO files from SVG

## Icon Design

The icon features:
- Mars-inspired gradient background (deep reds and oranges)
- Large "M" letterform with lava-like gradient fill
- Horizontal beams representing structural analysis
- Wave pattern symbolizing modal vibrations
- Professional, modern aesthetic suitable for engineering software

## Regenerating Icons

If you need to regenerate the PNG and ICO files from the SVG source:

```bash
cd resources/icons
python generate_icons.py
```

**Requirements:**
- Python 3.7+
- cairosvg (`pip install cairosvg`)
- Pillow (`pip install pillow`)

## Usage in Application

The icon is automatically loaded by the application at startup. The code attempts to load icons in this order:
1. `mars_icon.ico` (preferred for Windows)
2. `mars_128.png` (fallback)
3. `mars_64.png` (fallback)

See `src/ui/application_controller.py` for implementation details.

## Modifying the Icon

To modify the icon design:
1. Edit `mars_logo.svg` directly (any SVG editor or text editor)
2. Run `python generate_icons.py` to regenerate all PNG/ICO files
3. Restart the application to see changes

The SVG uses standard web fonts (Segoe UI, Roboto, etc.) and should render consistently across platforms.

