from PIL import Image, ImageDraw, ImageFont
import textwrap
import os
import regex  # Better than re for emojis

def is_emoji(char):
    return regex.match(r"\p{Emoji}", char)

def generate_caption_image(caption, output_path, video_width, font_path, emoji_font_path, font_size=36, max_width_ratio=0.85, margin=10):
    max_text_width = int(video_width * max_width_ratio)

    main_font = ImageFont.truetype(font_path, font_size)
    emoji_font = ImageFont.truetype(emoji_font_path, font_size)

    # Wrap lines
    wrapped_lines = []
    for line in caption.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=40))

    # Dummy canvas for measuring
    dummy_img = Image.new("RGBA", (video_width, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy_img)

    line_metrics = []
    for line in wrapped_lines:
        width = 0
        max_height = 0
        for char in line:
            font = emoji_font if is_emoji(char) else main_font
            w, h = draw.textsize(char, font=font)
            width += w
            max_height = max(max_height, h)
        line_metrics.append((width, max_height))

    total_height = sum(h for _, h in line_metrics) + margin * (len(line_metrics) - 1)
    img_height = total_height + 2 * margin
    img = Image.new("RGBA", (video_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    y = margin
    for idx, line in enumerate(wrapped_lines):
        line_width, line_height = line_metrics[idx]
        x = (video_width - line_width) // 2
        for char in line:
            font = emoji_font if is_emoji(char) else main_font
            w, _ = draw.textsize(char, font=font)
            draw.text((x, y), char, font=font, fill="black")
            x += w
        y += line_height + margin

    img.save(output_path)
    return output_path, img_height
