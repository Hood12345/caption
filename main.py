from flask import Flask, request, send_file, jsonify
import os
import uuid
import subprocess
import traceback
from caption_utils import generate_caption_image

app = Flask(__name__)

UPLOAD_DIR = "/tmp"
FONT_PATH = "Inter-ExtraLight.ttf"       # Your main font
EMOJI_FONT_PATH = "Twemoji.ttf"          # Emoji font

@app.route("/caption", methods=["POST"])
def caption():
    if 'file' not in request.files or 'caption' not in request.form:
        return jsonify({'error': 'Missing file or caption'}), 400

    try:
        video = request.files['file']
        caption = request.form['caption']

        input_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{input_id}.mp4")
        caption_img_path = os.path.join(UPLOAD_DIR, f"{input_id}_caption.png")
        output_path = os.path.join(UPLOAD_DIR, f"{input_id}_captioned.mp4")

        video.save(input_path)
        print(f"[INFO] Video saved at {input_path}")

        # Generate caption image
        generate_caption_image(caption, caption_img_path, FONT_PATH, EMOJI_FONT_PATH)

        # Overlay caption image on top of video
        subprocess.run([
            "ffmpeg", "-i", input_path, "-i", caption_img_path,
            "-filter_complex", "overlay=(main_w-overlay_w)/2:10",
            "-c:a", "copy", "-preset", "ultrafast",
            "-y", output_path
        ], check=True, timeout=60)

        if not os.path.exists(output_path):
            raise Exception("Failed to generate captioned video.")

        return send_file(output_path, mimetype="video/mp4", as_attachment=True)

    except subprocess.TimeoutExpired as te:
        print(f"[ERROR] ffmpeg timed out: {te}")
        traceback.print_exc()
        return jsonify({"error": "ffmpeg process timed out"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        for f in [input_path, output_path, caption_img_path]:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as ce:
                print(f"[WARN] Could not delete {f}: {ce}")

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
