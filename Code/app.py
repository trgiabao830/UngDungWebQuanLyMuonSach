from flask import Flask, render_template, request, redirect, url_for, flash, session
import psycopg2
from psycopg2 import sql
from datetime import datetime

app = Flask(__name__)
app.secret_key = '5432'

# Database 
DB_NAME = 'QuanLyThuVien'
DB_HOST = 'localhost'
DB_PORT = '5432'
TABLE_NAME = 'tbl_muonsach'

def get_db_connection():
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=session['db_user'],
        password=session['db_password'],
        host=DB_HOST,
        port=DB_PORT
    )
    return conn

# Hàm chuyển đổi định dạng ngày từ dd/mm/yyyy sang yyyy-mm-dd
def convert_to_db_format(date_str):
    try:
        return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
    except ValueError:
        return None

# Hàm chuyển đổi định dạng ngày từ yyyy-mm-dd sang dd/mm/yyyy
def convert_to_display_format(date_obj):
    if date_obj:
        return date_obj.strftime("%d/%m/%Y")
    return ""

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    db_user = request.form['username']
    db_password = request.form['password']

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=db_user,
            password=db_password,
            host=DB_HOST,
            port=DB_PORT
        )
        conn.close()  

        session['db_user'] = db_user
        session['db_password'] = db_password
        session['logged_in'] = True

        return redirect(url_for('library_management'))
    except psycopg2.OperationalError:
        flash('Thông tin đăng nhập cơ sở dữ liệu không hợp lệ')
        return redirect(url_for('login'))

@app.route('/library')
def library_management():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM {TABLE_NAME}")
    rows = cur.fetchall()
    conn.close()

    # Chuyển đổi ngày tháng từ DB format (yyyy-mm-dd) sang dd/mm/yyyy
    for i, row in enumerate(rows):
        # Chuyển tuple thành list để có thể thay đổi giá trị
        row_list = list(row)
        row_list[4] = convert_to_display_format(row_list[4])  # Ngày mượn
        row_list[5] = convert_to_display_format(row_list[5])  # Ngày trả
        rows[i] = tuple(row_list)  # Gán lại tuple đã thay đổi

    return render_template('library.html', rows=rows)

@app.route('/add', methods=['POST'])
def add_book():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    mssv = request.form['mssv']
    ten_sv = request.form['ten_sv']
    ten_sach = request.form['ten_sach']
    ngay_muon = convert_to_db_format(request.form['ngay_muon'])
    ngay_tra = convert_to_db_format(request.form['ngay_tra']) or None
    
    conn = get_db_connection()
    cur = conn.cursor()
    query = sql.SQL("INSERT INTO {table} (mssv, ten_sv, ten_sach, ngay_muon, ngay_tra) VALUES (%s, %s, %s, %s, %s)").format(
        table=sql.Identifier(TABLE_NAME)
    )
    cur.execute(query, (mssv, ten_sv, ten_sach, ngay_muon, ngay_tra))
    conn.commit()
    conn.close()
    return redirect(url_for('library_management'))

@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update_book(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(f"SELECT * FROM {TABLE_NAME} WHERE id = %s", (id,))
    book = cur.fetchone()
    conn.close()

    if request.method == 'POST':
        mssv = request.form['mssv']
        ten_sv = request.form['ten_sv']
        ten_sach = request.form['ten_sach']
        ngay_muon = convert_to_db_format(request.form['ngay_muon'])
        ngay_tra = convert_to_db_format(request.form['ngay_tra']) or None
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = sql.SQL("""
            UPDATE {table}
            SET mssv = %s, ten_sv = %s, ten_sach = %s, ngay_muon = %s, ngay_tra = %s
            WHERE id = %s
        """).format(table=sql.Identifier(TABLE_NAME))
        
        cur.execute(query, (mssv, ten_sv, ten_sach, ngay_muon, ngay_tra, id))
        conn.commit()
        conn.close()
        
        flash("Cập nhật thành công!")
        return redirect(url_for('library_management'))

    return render_template('update_book.html', book=book, convert_to_display_format=convert_to_display_format)


@app.route('/delete/<int:id>')
def delete_book(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    query = sql.SQL("DELETE FROM {table} WHERE id = %s").format(
        table=sql.Identifier(TABLE_NAME)
    )
    cur.execute(query, (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('library_management'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
