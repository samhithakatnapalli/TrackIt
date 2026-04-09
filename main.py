from flask import Flask,render_template,request,redirect,url_for
import psycopg2,os
from psycopg2 import pool

app = Flask(__name__)

db_pool = None

def init_pool():
    global db_pool
    db_pool = pool.SimpleConnectionPool(
        1, 10,
        os.environ["DATABASE_URL"],
        sslmode="require"
    )

# opening database
def get_db():
    if db_pool is None:
        init_pool()
    conn = db_pool.getconn()
    conn.autocommit = True
    return conn

# # setting up PostgreSQL database
def db_setup():
    connection = get_db()
    cursor = connection.cursor()

    cursor.execute('''
                    CREATE TABLE IF NOT EXISTS storage (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    list_name TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    category TEXT
                )
                ''')

    cursor.close()
    db_pool.putconn(connection)

file_data = {
    'tbr': ('tbr','TBR'),
    'to_watch': ('to_watch','To Watch'),
    'read': ('read','Read'),
    'watched': ('watched','Watched'),
}

# home page
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/home_page')
def home_page():
    user_name = (request.args.get('user_name') or '').title()
    if not user_name:
        return render_template('index.html')
    return render_template('home_page.html', user_name=user_name)

@app.route('/tbr')
def tbr():
    category = (request.args.get('category') or '').strip().lower()
    return render_template('tbr.html',user_name=request.args.get('user_name'), category=category)

@app.route('/to_watch')
def to_watch():
    category = (request.args.get('category') or '').strip().lower()
    return render_template('to_watch.html',user_name=request.args.get('user_name'), category=category)

@app.route('/read')
def read():
    category = (request.args.get('category') or '').strip().lower()
    return render_template('read.html',user_name=request.args.get('user_name'), category=category)

@app.route('/watched')
def watched():
    category = (request.args.get('category') or '').strip().lower()
    return render_template('watched.html',user_name=request.args.get('user_name'), category=category)

# list page
@app.route('/list_page/<list_name>')
def list_page(list_name):
    category = (request.args.get('category') or '').strip().lower()
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',category=category,user_name=request.args.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]
    
    connection = get_db()
    cursor = connection.cursor()

    if category:
        cursor.execute(
            'SELECT title, author FROM storage where list_name = %s AND user_name = %s AND category = %s', 
            (list_name, request.args.get('user_name'), category)
        )
    else:
        cursor.execute(
            'SELECT title, author FROM storage where list_name = %s AND user_name = %s', 
            (list_name, request.args.get('user_name'))
        )

    rows = cursor.fetchall()  # list of sqlite3.Row objects (not in dict format)
    cursor.close()
    db_pool.putconn(connection)

    # converting list of sqlite3.Row objects to list of dicts
    data = [{'title': row[0], 'author': row[1]} for row in rows]

    # sorting by title
    sorted_list = sorted(data, key=lambda x: x['title'])
    return render_template('status.html', category=category, tbr_books=sorted_list, user_name=request.args.get('user_name'), display_name=display_name, key_name=key_name, show_list=True, show_delete=False)

# taking user input from search box for all lists
@app.route('/handle-action/<list_name>', methods=['POST'])
def add_and_search_item(list_name):
    # get title and author from form, convert to title case
    action = request.form.get('action')
    title = (request.form.get('title') or '').strip()
    author = (request.form.get('author') or '').title()
    category = (request.form.get('category') or '').strip().lower()
    
    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',category=category,user_name=request.form.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]

    # selecting action to perform based on user input
    ## add item to list
    if action == 'add':
        if title != '':
            connection = get_db()
            cursor = connection.cursor()

            cursor.execute(
                'INSERT INTO storage (title, author, list_name, user_name, category) VALUES (%s, %s, %s, %s, %s)', 
                (title, author, list_name, request.form.get('user_name'), category if category else None)
            )

            cursor.close()
            db_pool.putconn(connection)

        return redirect(url_for('list_page', list_name=list_name, user_name=request.form.get('user_name'), category=category))
    
    ## search for item in list
    elif action == 'search':
        connection = get_db()
        cursor = connection.cursor()

        if author:
            if category:
                cursor.execute(
                    'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s AND category = %s',
                    (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'), category)
                )
            else:
                cursor.execute(
                    'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s',
                    (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'))
                )
        else:
            if category:
                cursor.execute(
                    'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND list_name = %s AND user_name = %s AND category = %s',
                    (title.lower().strip(), list_name, request.form.get('user_name'), category)
                )
            else:
                cursor.execute(
                    'SELECT title, author FROM storage where TRIM(LOWER(title)) = %s AND list_name = %s AND user_name = %s',
                    (title.lower().strip(), list_name, request.form.get('user_name'))
                )
        
        matches = [{'title': row[0], 'author': row[1]} for row in cursor.fetchall()]
        cursor.close()
        db_pool.putconn(connection)

        if matches:
            return render_template('status.html', category=category, user_name=request.form.get('user_name'), key_name=key_name, display_name=display_name, matches=matches, message='Item(s) found in list.', show_delete=True, show_list=False)
        else:
            return render_template('status.html', category=category, user_name=request.form.get('user_name'), key_name=key_name, message='Item not found. Try adding it to the list first.', show_list=False, show_delete=False)
        
# delete item from list
@app.route('/delete/<list_name>', methods=['POST'])
def delete_item(list_name):
    title = (request.form.get('title') or '').strip()
    author = (request.form.get('author') or '').title()
    category = (request.form.get('category') or '').strip().lower()

    if list_name not in file_data:
        return render_template('status.html', message='Invalid list name.',category=category,user_name=request.form.get('user_name'),show_list=False, show_delete=False)
    key_name, display_name = file_data[list_name]

    connection = get_db()
    cursor = connection.cursor()

    if author:
        if category:
            cursor.execute(
                'DELETE FROM storage WHERE TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s AND category = %s',
                (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'), category)
            )
        else:
            cursor.execute(
                'DELETE FROM storage WHERE TRIM(LOWER(title)) = %s AND TRIM(LOWER(author)) = %s AND list_name = %s AND user_name = %s',
                (title.lower().strip(), author.lower().strip(), list_name, request.form.get('user_name'))
            )
    else:
        if category:
            cursor.execute(
                'DELETE FROM storage WHERE TRIM(LOWER(title)) = %s AND list_name = %s AND user_name = %s AND category = %s',
                (title.lower().strip(), list_name, request.form.get('user_name'), category)
            )
        else:
            cursor.execute(
                'DELETE FROM storage WHERE TRIM(LOWER(title)) = %s AND list_name = %s AND user_name = %s',
                (title.lower().strip(), list_name, request.form.get('user_name'))
            )

    if cursor.rowcount > 0 :
        if author:
            message=f'{title} by {author} deleted successfully'
        else:
            message=f'{title} deleted successfully'
    else:
        if author:
            message=f'"{title} by {author}" not found. Try adding it to the list first.'
        else:
            message=f'"{title}" not found. Try adding it to the list first.'

    cursor.close()
    db_pool.putconn(connection)

    return render_template('status.html', category=category, user_name=request.form.get('user_name'), message=message, display_name=display_name, key_name=key_name, show_list=False, show_delete=False)


if __name__ == '__main__':
    init_pool()
    db_setup()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
