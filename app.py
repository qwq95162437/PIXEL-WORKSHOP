from flask import Flask, request, render_template_string, redirect, Response
import sqlite3
from pathlib import Path
from datetime import datetime
from functools import wraps

app = Flask(__name__)

DB_DIR = Path("instance")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "messages.db")


# 管理员账号密码
ADMIN_USERNAME = "qwq861186"
ADMIN_PASSWORD = "QWE.rty.777836"


def check_auth(username, password):
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def authenticate():
    return Response(
        "需要登录才能访问后台",
        401,
        {"WWW-Authenticate": 'Basic realm="Admin Login"'}
    )


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization

        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()

        return f(*args, **kwargs)

    return decorated


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/api/message", methods=["POST"])
def save_message():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    content = request.form.get("content", "").strip()

    if not name or not email or not subject or not content:
        return redirect("/contact.html?status=empty")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (name, email, subject, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        name,
        email,
        subject,
        content,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    return redirect("/contact.html?status=success")


@app.route("/admin/messages")
@requires_auth
def list_messages():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, email, subject, content, created_at
        FROM messages
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <title>留言管理后台</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                padding: 30px;
                background: #f5f5f5;
            }

            h1 {
                margin-bottom: 20px;
            }

            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
            }

            th, td {
                border: 1px solid #ddd;
                padding: 10px;
                text-align: left;
                vertical-align: top;
            }

            th {
                background: #222;
                color: white;
            }

            tr:nth-child(even) {
                background: #f9f9f9;
            }
        </style>
    </head>
    <body>
        <h1>留言列表</h1>

        <table>
            <tr>
                <th>ID</th>
                <th>姓名</th>
                <th>邮箱</th>
                <th>主题</th>
                <th>内容</th>
                <th>时间</th>
            </tr>

            {% for row in rows %}
            <tr>
                <td>{{ row[0] }}</td>
                <td>{{ row[1] }}</td>
                <td>{{ row[2] }}</td>
                <td>{{ row[3] }}</td>
                <td>{{ row[4] }}</td>
                <td>{{ row[5] }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """

    return render_template_string(html, rows=rows)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)