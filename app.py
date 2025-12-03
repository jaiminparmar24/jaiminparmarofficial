import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import qrcode
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = "change_this_secret_in_production"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2MB limit for any uploads (if added later)

def is_valid_url(u: str) -> bool:
    u = u.strip()
    return u.startswith("http://") or u.startswith("https://")

def save_qr_png(text: str, fg="#000000", bg="#ffffff", box_size=10, border=4):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color=fg, back_color=bg).convert("RGB")
    filename = f"qr_{int(datetime.utcnow().timestamp())}.png"
    path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(filename))
    img.save(path)
    return filename, path

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            flash("Please enter a URL.", "danger")
            return redirect(url_for("index"))

        # agar user sirf example.com type kare to automatically https add kar dena (optional)
        if not (url.startswith("http://") or url.startswith("https://")):
            url = "https://" + url

        if not is_valid_url(url):
            flash("Invalid URL. Make sure it starts with http:// or https://", "danger")
            return redirect(url_for("index"))

        # colors/size optional fields (simple defaults)
        fg = request.form.get("fg_color", "#000000")
        bg = request.form.get("bg_color", "#ffffff")
        try:
            size = int(request.form.get("size", 10))
            border = int(request.form.get("border", 4))
        except:
            size, border = 10, 4

        try:
            filename, path = save_qr_png(url, fg=fg, bg=bg, box_size=size, border=border)
            return render_template("result.html", url=url, filename=filename)
        except Exception as e:
            print("Error generating QR:", e)
            flash("Error generating QR. Try again.", "danger")
            return redirect(url_for("index"))

    return render_template("index.html")

@app.route("/download/<filename>")
def download_file(filename):
    safe = secure_filename(filename)
    path = os.path.join(app.config["UPLOAD_FOLDER"], safe)
    if not os.path.exists(path):
        flash("File not found.", "danger")
        return redirect(url_for("index"))
    return send_file(path, as_attachment=True, download_name=safe, mimetype="image/png")

if __name__ == "__main__":
    app.run(debug=True)
