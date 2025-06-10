from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap
import os
import regex

def is_emoji(char):
    return regex.match(r"\p{Emoji}", char)

def emoji_to_filename(emoji):
    codepoints = '-'.join(f"{ord(c):x}" for c in emoji)
    return f"{codepoints}.png"

def generate_caption_image(caption, output_path, video_width, font_path, emoji_dir, font_size=36, max_width_ratio=0.85, margin=10):
    main_font = ImageFont.truetype(font_path, font_size)

    # Wrap lines
    wrapped_lines = []
    for line in caption.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=40))

    dummy_img = Image.new("RGBA", (video_width, 200), (255, 255, 255, 0))
    draw = ImageDraw.Draw(dummy_img)

    line_metrics = []
    char_maps = []

    for line in wrapped_lines:
        width = 0
        height = 0
        char_map = []

        for char in line:
            if is_emoji(char):
                filename = emoji_to_filename(char)
                path = os.path.join(emoji_dir, filename)
                if os.path.exists(path):
                    img = Image.open(path).convert("RGBA")
                    scale = font_size / img.height
                    emoji_img = img.resize((int(img.width * scale), font_size), Image.Resampling.LANCZOS)
                    w, h = emoji_img.size
                    char_map.append((char, 'emoji', emoji_img))
                else:
                    w, h = main_font.getbbox(char)[2:]
                    char_map.append((char, 'text', main_font))
            else:
                w, h = main_font.getbbox(char)[2:]
                char_map.append((char, 'text', main_font))

            width += w
            height = max(height, h)

        char_maps.append(char_map)
        line_metrics.append((width, height))

    total_height = sum(h for _, h in line_metrics) + margin * (len(line_metrics) - 1)
    img_height = total_height + 2 * margin
    img = Image.new("RGBA", (video_width, img_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)

    y = margin
    for idx, char_map in enumerate(char_maps):
        line_width, line_height = line_metrics[idx]
        x = (video_width - line_width) // 2

        for char, kind, content in char_map:
            if kind == 'emoji':
                img.paste(content, (x, y), content)
                x += content.size[0]
            else:
                w = content.getbbox(char)[2]
                draw.text((x, y), char, font=content, fill="black")
                x += w

        y += line_height + margin

    img.save(output_path)
    return output_path, img_height
