from flask import Flask, render_template, request, send_file, Response
import yt_dlp
import os
import uuid

app = Flask(__name__)
DOWNLOAD_DIR = "downloads"

if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    data = request.get_json()
    url = data.get("url")
    media_type = data.get("media")

    file_id = str(uuid.uuid4())
    filename = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")

    options = {
        "format": "bestaudio/best" if media_type == "audio" else "bestvideo+bestaudio/best",
        "outtmpl": filename,
        "quiet": True,
        "noplaylist": True
    }

    if media_type == "audio":
        options["postprocessors"] = [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(info)
            if media_type == "audio":
                downloaded_file = downloaded_file.rsplit(".", 1)[0] + ".mp3"

        def generate():
            with open(downloaded_file, "rb") as f:
                yield from f
            os.remove(downloaded_file)

        return Response(generate(), headers={
            "Content-Disposition": f"attachment; filename=\\"{os.path.basename(downloaded_file)}\\"",
            "Content-Type": "application/octet-stream"
        })

    except yt_dlp.utils.DownloadError:
        return {"error": "⚠️ The video is unavailable or restricted. Please try another link."}, 500
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}, 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
