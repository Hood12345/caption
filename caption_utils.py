from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def generate_caption_image(caption, output_path, video_width, font_path, emoji_font_path, font_size=36, max_width_ratio=0.85, margin=10):
    max_text_width = int(video_width * max_width_ratio)

    # Load fonts
    main_font = ImageFont.truetype(font_path, font_size)
    emoji_font = ImageFont.truetype(emoji_font_path, font_size)

    # Dummy canvas for layout
    dummy_img = Image.new("RGBA", (video_width, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy_img)

    # Wrap lines
    wrapped_lines = []
    for line in caption.split("\n"):
        wrapped = textwrap.wrap(line, width=40)
        wrapped_lines.extend(wrapped)

    # Measure lines
    line_heights = []
    line_widths = []
    for line in wrapped_lines:
        w, h = draw.textsize(line, font=main_font)
        line_widths.append(w)
        line_heights.append(h)

    total_height = sum(line_heights) + margin * (len(line_heights) - 1)
    img_height = total_height + 2 * margin

    # Final image
    img = Image.new("RGBA", (video_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    y = margin
    for i, line in enumerate(wrapped_lines):
        x = (video_width - line_widths[i]) // 2
        draw.text((x, y), line, font=main_font, fill="black")
        y += line_heights[i] + margin

    img.save(output_path)
    return output_path, img_height
