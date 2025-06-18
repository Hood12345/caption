# caption_utils.py ────────────────────────────────────────────────────────────
from PIL import Image, ImageDraw, ImageFont, ImageOps
import textwrap, os, regex, math

# ▶︎ Compatibility layer for old Pillow (<10) vs new (≥10)
try:
    from PIL import ImageResampling       # Pillow ≥10
    RESAMPLE = ImageResampling.LANCZOS
except ImportError:                       # Pillow <10
    RESAMPLE = Image.LANCZOS


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
    scale_factor: int = 6,        # super-sampling factor
    max_width_ratio: float = 0.85,
    margin: int = 10,
    TRACKING: int = -1            # negative = tight kerning
):
    """
    Render a razor-sharp PNG caption strip that remains ultra-thin but deep black.
    Returns (output_path, caption_height_at_final_scale)
    """

    # 1. High-res setup -------------------------------------------------------
    fs_hr        = font_size   * scale_factor
    video_w_hr   = video_width * scale_factor
    margin_hr    = margin      * scale_factor
    track_hr     = TRACKING    * scale_factor
    font_hr      = ImageFont.truetype(font_path, fs_hr)

    # thin stroke (fills grey edge pixels but keeps stroke width)
    stroke_px_hr = max(1, scale_factor // 2)  # e.g. scale 6 → stroke 3

    # 2. Line wrapping --------------------------------------------------------
    wrapped_lines = []
    for line in caption.split("\n"):
        wrapped_lines.extend(textwrap.wrap(line, width=40))

    # 3. Measure & map glyphs -------------------------------------------------
    line_metrics, line_maps = [], []
    for line in wrapped_lines:
        glyphs, line_w, line_h = [], 0, 0
        for ch in line:
            if is_emoji(ch):
                fname = os.path.join(emoji_dir, emoji_to_filename(ch))
                if os.path.exists(fname):
                    img = Image.open(fname).convert("RGBA")
                    scale = fs_hr / img.height
                    emoji_img = img.resize(
                        (int(img.width * scale), fs_hr),
                        RESAMPLE
                    )
                    w, h = emoji_img.size
                    glyphs.append(("emoji", emoji_img, w))
                else:
                    w, h = font_hr.getbbox(ch)[2:]
                    glyphs.append(("text", ch, w))
            else:
                w, h = font_hr.getbbox(ch)[2:]
                glyphs.append(("text", ch, w))

            line_w += w + track_hr
            line_h  = max(line_h, h)

        line_w -= track_hr                      # trim trailing tracking
        line_maps.append(glyphs)
        line_metrics.append((line_w, line_h))

    # 4. Create high-res transparent canvas -----------------------------------
    total_h   = sum(h for _, h in line_metrics) + margin_hr * (len(line_metrics)-1)
    canvas_h  = total_h + 2 * margin_hr
    img_hr    = Image.new("RGBA", (video_w_hr, canvas_h), (255, 255, 255, 0))
    draw_hr   = ImageDraw.Draw(img_hr)

    # 5. Render text & emojis --------------------------------------------------
    y = margin_hr
    for (line_w, line_h), glyphs in zip(line_metrics, line_maps):
        x = (video_w_hr - line_w) // 2
        for kind, content, w in glyphs:
            if kind == "emoji":
                img_hr.paste(content, (x, y), content)
            else:
                # draw once with stroke to deepen black but keep thin weight
                draw_hr.text(
                    (x, y),
                    content,
                    font=font_hr,
                    fill="black",
                    stroke_width=stroke_px_hr,
                    stroke_fill="black"
                )
            x += w + track_hr
        y += line_h + margin_hr

    # 6. Downsample to final size ---------------------------------------------
    final_h   = math.ceil(canvas_h / scale_factor)
    img_final = img_hr.resize((video_width, final_h), RESAMPLE)
    img_final.save(output_path, "PNG")

    return output_path, final_h
