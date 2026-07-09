from flask import Flask, request, redirect, Response, render_template, url_for
import sqlite3
from pathlib import Path
from datetime import datetime
from functools import wraps
import math

app = Flask(__name__)

DB_DIR = Path("instance")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = str(DB_DIR / "messages.db")


# 前端页面路由
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/software")
def software():
    return render_template("software.html")

@app.route("/games")
def games():
    return render_template("games.html")

@app.route("/log")
def log():
    return render_template("log.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    status = request.args.get("status", "")
    return render_template("contact.html", status=status)

@app.route("/pixel-adventure")
def pixel_adventure():
    return render_template("pixel-adventure.html")

@app.route("/puzzle-temple")
def puzzle_temple():
    return render_template("puzzle-temple.html")

@app.route("/indie-lab")
def indie_lab():
    return render_template("indie-lab.html")


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


# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# 新增字段
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
            is_read INTEGER NOT NULL DEFAULT 0,
            is_deleted INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()


# 查留言总数
def count_messages(keyword="", status="all"):
    conn = get_db_connection()
    cur = conn.cursor()
     
    sql = " SELECT COUNT(*) FROM messages WHERE is_deleted = 0"
    params = []

    if status == "read":
        sql += "AND is_read = 1"
    elif status == "unread":
        sql += "AND is_read = 0"

    if keyword:
        sql += """
        AND (
            name LIKE ?
            OR email LIKE ?
            OR subject LIKE ?
            OR content LIKE ?
        )
        """
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword, like_keyword])

    cur.execute(sql, params)
    total = cur.fetchone()[0]
    conn.close()
    return total


# 查留言列表
def get_messages(keyword="", status="all", page=1, per_page=10):
    conn = get_db_connection()
    cur = conn.cursor()

    sql = """
        SELECT id, name, email, subject, content, is_read, is_deleted, created_at, updated_at
        FROM messages
        WHERE is_deleted = 0
    """
    params = []

    if status == "read":
        sql += " AND is_read = 1"
    elif status == "unread":
        sql += " AND is_read = 0"
    
    if keyword:
        sql += """
        AND (
            name LIKE ?
            OR email LIKE ?
            OR subject LIKE ?
            OR content LIKE ?
        )
        """
        like_keyword = f"%{keyword}%"
        params.extend([like_keyword, like_keyword, like_keyword, like_keyword])

    sql += "ORDER BY id DESC LIMIT ? OFFSET ?"
    offset = (page - 1) * per_page
    params.extend([per_page, offset])

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows 


# 统计未读数
def count_unread_messages():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = 0 AND is_read = 0")
    total = cur.fetchone()[0]
    conn.close()
    return total


# 统计已读数
def count_read_messages():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM messages WHERE is_deleted = 0 AND is_read = 1")
    total = cur.fetchone()[0]
    conn.close()
    return total


# 标记已读/未读
def set_message_read(message_id, is_read):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE messages
        SET is_read = ?, updated_at = ?
        WHERE id = ? AND is_deleted = 0
    """, (
        1 if is_read else 0,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message_id
    ))
    conn.commit()
    conn.close()


# 逻辑删除
def soft_delete_message(message_id):
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE messages
        SET is_deleted = 1, updated_at = ?
        WHERE id = ?
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        message_id
    ))
    conn.commit()
    conn.close()


# 保存留言
@app.route("/api/message", methods=["POST"])
def save_message():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    subject = request.form.get("subject", "").strip()
    content = request.form.get("content", "").strip()

    if not name or not email or not subject or not content:
        return redirect(url_for("contact", status="empty"))
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cur.execute("""
            INSERT INTO messages (
                name, email, subject, content,
                is_read, is_deleted, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            email,
            subject,
            content,
            0,
            0,
            now,
            now
        ))
        conn.commit()
        conn.close()

        return redirect(url_for("contact", status="success"))

    except Exception:
        return redirect(url_for("contact", status="error"))


# 查留言总数/查留言列表/统计未读/统计已读路由
@app.route("/admin/messages")
@requires_auth
def list_messages():
    keyword = request.args.get("keyword", "").strip()
    status = request.args.get("status", "all").strip()
    page = request.args.get("page", 1, type=int)

    per_page = 10
    total = count_messages(keyword=keyword, status=status)
    total_pages = max(1, math.ceil(total / per_page))

    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    rows = get_messages(
        keyword=keyword,
        status=status,
        page=page,
        per_page=per_page
    )

    unread_count = count_unread_messages()
    read_count = count_read_messages()

    return render_template(
        "admin/messages.html",
        rows=rows,
        keyword=keyword,
        status=status,
        page=page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        unread_count=unread_count,
        read_count=read_count
    )


# 标记已读路由
@app.route("/admin/messages/<int:message_id>/read", methods=["POST"])
@requires_auth
def mark_message_read(message_id):
    set_message_read(message_id, True)
    return redirect(request.referrer or url_for("list_messages"))


# 标记未读路由
@app.route("/admin/messages/<int:message_id>/unread", methods=["POST"])
@requires_auth
def mark_message_unread(message_id):
    set_message_read(message_id, False)
    return redirect(request.referrer or url_for("list_messages"))


#删除留言路由
@app.route("/admin/messages/<int:message_id>/delete", methods=["POST"])
@requires_auth
def delete_message(message_id):
    soft_delete_message(message_id)
    return redirect(request.referrer or url_for("list_messages"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=False)