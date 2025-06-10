from flask import Flask, request, send_file, jsonify
import os
import uuid
import subprocess
import traceback
import cv2
from caption_utils import generate_caption_image

app = Flask(__name__)

UPLOAD_DIR = "/tmp"
FONT_PATH = "Inter-ExtraLight.ttf"
EMOJI_FONT_PATH = "Twemoji.ttf"
FALLBACK_Y = 390

def extract_top_y_from_frame(frame_path):
    print("[INFO] Analyzing frame with OpenCV...")
    img = cv2.imread(frame_path)
    if img is None:
        raise Exception("OpenCV could not load the frame.")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print("[WARN] No contours found. Using fallback Y.")
        return FALLBACK_Y

    top_y = min([cv2.boundingRect(c)[1] for c in contours])
    return max(10, top_y)

@app.route("/caption", methods=["POST"])
def caption():
    input_path = output_path = caption_img_path = frame_path = None
    if 'file' not in request.files or 'caption' not in request.form:
        return jsonify({'error': 'Missing file or caption'}), 400

    try:
        video = request.files['file']
        caption = request.form['caption']

        input_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{input_id}.mp4")
        caption_img_path = os.path.join(UPLOAD_DIR, f"{input_id}_caption.png")
        output_path = os.path.join(UPLOAD_DIR, f"{input_id}_captioned.mp4")
        frame_path = os.path.join(UPLOAD_DIR, f"{input_id}_frame.jpg")

        video.save(input_path)
        print(f"[INFO] Video saved at {input_path}")

        # Extract frame for analysis
        subprocess.run([
            "ffmpeg", "-i", input_path, "-vf", "select=eq(n\\,0)",
            "-q:v", "3", "-frames:v", "1", frame_path
        ], check=True)

        top_y = extract_top_y_from_frame(frame_path)

        # ✅ FIXED: Include output_path as required by your caption_utils.py
        caption_img_path, caption_height = generate_caption_image(
            caption, caption_img_path, 1080, FONT_PATH, EMOJI_FONT_PATH
        )

        overlay_y = max(10, top_y - caption_height - 10)
        print(f"[INFO] Overlay Y: {overlay_y}")

        # Overlay caption on video
        subprocess.run([
            "ffmpeg", "-i", input_path, "-i", caption_img_path,
            "-filter_complex", f"overlay=(main_w-overlay_w)/2:{overlay_y}",
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
        for f in [input_path, output_path, caption_img_path, frame_path]:
            try:
                if f and os.path.exists(f):
                    os.remove(f)
            except Exception as ce:
                print(f"[WARN] Could not delete {f}: {ce}")

@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
