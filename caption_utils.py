# caption_utils.py  ── replace ONLY the function below ─────────────────────────
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageResampling
import textwrap, os, regex, math

def is_emoji(char):
    return regex.match(r"\p{Emoji}", char)

def emoji_to_filename(emoji):
    return "-".join(f"{ord(c):x}" for c in emoji) + ".png"

def generate_caption_image(
    caption: str,
    output_path: str,
    video_width: int,
    font_path: str,
    emoji_dir: str,
    *,
    font_size: int = 36,
    scale_factor: int = 4,        # 🔄 was 3 → crisper at 4×
    max_width_ratio: float = 0.85,
    margin: int = 10,
    TRACKING: int = 2             # 🔄 uniform letter-spacing (px at 1×)
):
    """
    Renders caption at (scale_factor × video_width) then downsamples.
    Returns (output_path, caption_height_at_final_scale)
    """

    # 1.  High-res setup -------------------------------------------------------
    fs_hr = font_size * scale_factor
    video_w_hr = video_width * scale_factor
    margin_hr   = margin * scale_factor
    font_hr = ImageFont.truetype(font_path, fs_hr)

    # 2.  Line wrapping --------------------------------------------------------
    wrapped_lines = []
    for line in caption.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=40))

    # 3.  Measure & map glyphs -------------------------------------------------
    line_metrics, line_maps = [], []
    for line in wrapped_lines:
        line_w, line_h, glyphs = 0, 0, []
        for ch in line:
            if is_emoji(ch):
                fname = os.path.join(emoji_dir, emoji_to_filename(ch))
                if os.path.exists(fname):
                    img = Image.open(fname).convert("RGBA")
                    scale = fs_hr / img.height
                    emoji_img = img.resize(
                        (int(img.width * scale), fs_hr),
                        ImageResampling.LANCZOS
                    )
                    w, h = emoji_img.size
                    glyphs.append(("emoji", emoji_img, w))
                else:
                    w, h = font_hr.getbbox(ch)[2:]
                    glyphs.append(("text", ch, w))
            else:
                w, h = font_hr.getbbox(ch)[2:]
                glyphs.append(("text", ch, w))
            line_w += w + TRACKING * scale_factor
            line_h = max(line_h, h)
        line_w -= TRACKING * scale_factor  # remove trailing space
        line_metrics.append((line_w, line_h))
        line_maps.append(glyphs)

    # 4.  Create HR canvas -----------------------------------------------------
    total_h = sum(h for _, h in line_metrics) + margin_hr * (len(line_metrics) - 1)
    canvas_h_hr = total_h + 2 * margin_hr
    img_hr = Image.new("RGBA", (video_w_hr, canvas_h_hr), (255, 255, 255, 0))
    draw_hr = ImageDraw.Draw(img_hr)

    # 5.  Render text & emojis --------------------------------------------------
    y = margin_hr
    for (line_w, line_h), glyphs in zip(line_metrics, line_maps):
        x = (video_w_hr - line_w) // 2
        for kind, content, w in glyphs:
            if kind == "emoji":
                img_hr.paste(content, (x, y), content)
            else:
                draw_hr.text((x, y), content, font=font_hr, fill="black")
            x += w + TRACKING * scale_factor
        y += line_h + margin_hr

    # 6.  Downsample to final size ---------------------------------------------
    final_h = math.ceil(canvas_h_hr / scale_factor)
    img_final = img_hr.resize((video_width, final_h), ImageResampling.LANCZOS)
    img_final.save(output_path, "PNG")

    return output_path, final_h
