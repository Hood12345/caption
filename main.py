from flask import Flask, request, send_file, jsonify
import os
import subprocess
import uuid
import cv2

app = Flask(__name__)

UPLOAD_DIR = "/tmp"
FONT_PATH = "Inter_28pt-Thin.ttf"
FONT_SIZE = 48
MARGIN = 10
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
        raise Exception("No video content found in the frame.")

    top_y = min([cv2.boundingRect(c)[1] for c in contours])
    print(f"[INFO] Top Y of video content: {top_y}")
    return top_y

@app.route("/caption", methods=["POST"])
def caption():
    if 'file' not in request.files or 'caption' not in request.form:
        return jsonify({'error': 'Missing file or caption'}), 400

    try:
        video = request.files['file']
        caption = request.form['caption']

        input_id = str(uuid.uuid4())
        input_path = os.path.join(UPLOAD_DIR, f"{input_id}.mp4")
        frame_path = os.path.join(UPLOAD_DIR, f"{input_id}_frame.jpg")
        output_path = os.path.join(UPLOAD_DIR, f"{input_id}_captioned.mp4")

        video.save(input_path)
        print(f"[INFO] Video saved at {input_path}")

        if not os.path.exists(FONT_PATH):
            raise FileNotFoundError(f"[ERROR] Font not found at {FONT_PATH}")

        # Step 1: Extract middle frame (10th frame)
        print("[INFO] Extracting frame for content detection...")
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-vf", "select=eq(n\\,10)", "-vframes", "1",
            "-q:v", "2", frame_path,
            "-y"
        ], check=True, timeout=30)

        # Step 2: Find top of actual video content
        top_y = extract_top_y_from_frame(frame_path)
        caption_y = max(top_y - FONT_SIZE - MARGIN, 10)

        # Step 3: Sanitize caption
        safe_caption = caption.replace("'", "\\'").replace(":", "\\:")

        # Step 4: Generate video with caption
        drawtext = (
            f"drawtext=fontfile='{FONT_PATH}':text='{safe_caption}':"
            f"fontcolor=black:fontsize={FONT_SIZE}:x=(w-text_w)/2:y={caption_y}"
        )
        print(f"[INFO] Applying caption at y={caption_y}")

        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-vf", drawtext,
            "-c:a", "copy",
            "-preset", "ultrafast",
            "-y", output_path
        ], check=True, timeout=60)

        if not os.path.exists(output_path):
            raise Exception("Failed to generate captioned video.")

        return send_file(output_path, mimetype="video/mp4", as_attachment=True)

    except subprocess.TimeoutExpired as te:
        print(f"[ERROR] ffmpeg timed out: {te}")
        return jsonify({"error": "ffmpeg process timed out"}), 500
    except Exception as e:
        print(f"[ERROR] {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        for f in [input_path, output_path, frame_path]:
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
