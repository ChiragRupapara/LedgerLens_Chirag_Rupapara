from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


def add_watermark(image_path: str, doc_id: str) -> str:
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    stamp_text = f"{doc_id} | {timestamp}"

    # Scale font size relative to image width, so it's visible on any resolution
    font_size = max(16, img.width // 40)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except OSError:
        font = ImageFont.load_default()

    margin = 10
    text_bbox = draw.textbbox((0, 0), stamp_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    x = img.width - text_width - margin
    y = img.height - text_height - margin

    # Draw a semi-opaque dark background box behind the text so it's readable
    # on any background color (white receipts, dark receipts, etc.)
    box_padding = 4
    draw.rectangle(
        [x - box_padding, y - box_padding, x + text_width + box_padding, y + text_height + box_padding],
        fill=(0, 0, 0),
    )
    draw.text((x, y), stamp_text, fill=(255, 255, 255), font=font)

    original_path = Path(image_path)
    watermarked_path = original_path.parent / f"watermarked{original_path.suffix}"
    img.save(watermarked_path)

    return str(watermarked_path)


if __name__ == "__main__":
    # Quick manual test
    import sys
    result = add_watermark(sys.argv[1], "TEST123")
    print(f"Watermarked image saved to: {result}")