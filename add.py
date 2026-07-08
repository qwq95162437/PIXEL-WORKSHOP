from flask import Flask, render_template, request, redirect, url_for, flash
import smtplib
from email.mime.text import MIMEText
from email.header import Header

app = Flask(__name__)
app.secret_key = "your-secret-key"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contact.html")
def contact_page():
    return render_template("contact.html")

@app.route("/contact", methods=["POST"])
def contact_submit():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    topic = request.form.get("topic", "").strip()
    message = request.form.get("message", "").strip()

    if not name or not email or not topic or not message:
        flash("请填写完整信息")
        return redirect(url_for("contact_page"))

    body = f"""
昵称/姓名: {name}
邮箱: {email}
主题: {topic}

留言内容:
{message}
"""

    sender_email = "你的邮箱@gmail.com"
    sender_password = "你的应用专用密码"
    receiver_email = "qwq861186@gmail.com"

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = Header(sender_email, "utf-8")
    msg["To"] = Header(receiver_email, "utf-8")
    msg["Subject"] = Header(f"网站留言：{topic}", "utf-8")

    try:
        smtp = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        smtp.login(sender_email, sender_password)
        smtp.sendmail(sender_email, [receiver_email], msg.as_string())
        smtp.quit()

        flash("留言发送成功")
    except Exception as e:
        flash(f"留言发送失败：{e}")

    return redirect(url_for("contact_page"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)