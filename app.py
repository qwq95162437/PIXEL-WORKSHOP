from flask import Flask, request, render_template_string, redirect, url_for
import sqlite3
from pathlib import Path
from datetime import datetime

app = Flask(__name__)

DB_DIR = Path("instance")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "messages.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur =conn.cursor()
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
    cur =conn.cursor()
    cur.execute("""
        INSERT INTO messages (name, email, subject, content, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, email, subject, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return redirect("/contact.html?status=success")

@app.route("/admin/messages")
def list_messages():
    conn =sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, name, email, subject, content, created_at
        FROM messages
        ORDER BY id DESC
    """)
    rows = cur.fetchall()
    conn.close()

    html = """
    <h1>留言列表</h1>
    <table border="1" cellpadding="8" cellspacing="0">
      <tr>
        <th>ID</th><th>姓名</th><th>邮箱</th><th>主题</th><th>内容</th><th>时间</th>
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
    """
    
    return render_template_string(html, rows=rows)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)