import sqlite3
from flask import Flask, Blueprint, render_template, request, url_for, flash, redirect, jsonify
from werkzeug.exceptions import abort
import functools
from time import sleep
import uuid, time
from libgravatar import Gravatar 

app = Flask(__name__)

app.secret_key = SECRET_KEY

ips = {}

#GRAVATAR
def gravatar(mail):
  try:
    g = Gravatar(mail)
    return g.get_image()
  except:
    pass

def gravatar2(mail):
  try:
    g = Gravatar(mail)
    return g.get_image(size=500)
  except:
    pass

#CONEXÃO DA DATABASE
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection_login():
    conn = sqlite3.connect('database/database.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_db_connection_ip():
    conn = sqlite3.connect('ips/database.db')
    conn.row_factory = sqlite3.Row
    return conn

#POST
def get_post(post_id):
    conn = get_db_connection()
    post = conn.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id, )).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return post

#USUÁRIO
def get_user(user_id):
    conn = get_db_connection_login()
    user = conn.execute('SELECT * FROM user WHERE id = ?',
                        (user_id, )).fetchone()
    conn.close()
    if post is None:
        abort(404)
    return user

def get_username():
  try:
    yip = request.headers.get('X-Forwarded-For', request.remote_addr)
    conn = get_db_connection_ip()
    logins = conn.execute('SELECT * FROM logins').fetchall()
    conn.close()
    list_of_ips = {}
    for login in logins:
        list_of_ips[login['ip']] = login['id']
    id = list_of_ips[yip]
    conn2 = get_db_connection_login()
    user = conn2.execute('SELECT * FROM user WHERE id = ?', (id, )).fetchone()
    conn2.close()

    if user['profile'] == None:
      lista = [user['name'], user['email'], id, '...']
    else:
      lista = [user['name'], user['email'], id, user['profile']]

    return lista
  except:
    lista = ['visitante', 'None', 'None', '...']
    return lista

#LOGIN OBRIGATÓRIO
def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        conn = get_db_connection_ip()
        logins = conn.execute('SELECT * FROM logins').fetchall()
        conn.close()
        yip = request.headers.get('X-Forwarded-For', request.remote_addr)
        list_of_ips = {}
        for login in logins:
            list_of_ips[login['ip']] = [login['id'], login['admin']]
        if not yip in list_of_ips:
            return redirect("/login")
        elif list_of_ips[yip][1] == "False":
            return redirect("/")
        return view(**kwargs)

    return wrapped_view

#TOTAL DE POSTS
def number_of_posts():
    number_of_posts = 0

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    for post in posts:
        number_of_posts += 1

    return number_of_posts

#INDEX
@app.route('/')
def index():
    user = get_username()
    if user[0] == "visitante":
        flash('Seja bem-vindo ao nosso site.')

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    conn2 = get_db_connection_login()
    users = conn2.execute('SELECT * FROM user').fetchall()
    conn2.close()

    user=get_username()

    return render_template('app.html', posts=posts, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#PAG. LOGIN
@app.route('/login', methods=('GET', 'POST'))
def login():
    yip = request.headers.get('X-Forwarded-For', request.remote_addr)
    conn = get_db_connection_ip()
    logins = conn.execute('SELECT * FROM logins').fetchall()
    conn.close()
    list_of_ips = {}
    for login in logins:
        list_of_ips[login['ip']] = login['id']
    if yip in list_of_ips.keys():
        if list_of_ips[yip] == "True":
            return redirect("/admin")
        else:
            return redirect("/")
    if request.method == "POST":
        conn =  get_db_connection_login()
        users = conn.execute('SELECT * FROM user').fetchall()
        conn.close()
        try:
            email = request.form['email']
            password = request.form['password']
        except Exception as e:
            print(e)
        else:
            try:
                for user in users:
                    if user['email'] == email and user['password'] == password:
                        conn = get_db_connection_ip()
                        if user['admin'] == "True":
                            conn.execute(
                                'INSERT INTO logins (ip, id, admin) VALUES (?, ?, ?)',
                                (request.headers.get('X-Forwarded-For', request.remote_addr), user['id'], 'True'))
                            conn.commit()
                            
                            return redirect("/admin")
                        else:
                            conn.execute(
                                'INSERT INTO logins (ip, id, admin) VALUES (?, ?, ?)',
                                (request.headers.get('X-Forwarded-For', request.remote_addr), user['id'], 'False'))
                            conn.commit()

                            return redirect("/")

                        conn.close()

            except Exception as e:
                print(e)
                flash(
                    'Por favor, verifique os seus dados de login e tente novamente.'
                )

    user=get_username()

    return render_template('login.html', numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#PAG. LOGOUT
@app.route('/logout', methods=('GET', 'POST'))
def logout():
    try:
        yip = request.headers.get('X-Forwarded-For', request.remote_addr)
        conn = get_db_connection_ip()
        conn.execute('DELETE FROM logins WHERE ip = ?', (yip, ))
        conn.commit()
        conn.close()

        del ips[request.headers.get('X-Forwarded-For', request.remote_addr)]

        return redirect("/")
    except:
        return redirect("/")
        pass

#PAG. REGISTRO
@app.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == "POST":
        try:
            email = request.form['email']
            password = request.form['password']
            name = request.form['name']
        except Exception as e:
            print(e)
        else:
            try:
                conn =  get_db_connection_login()
                users = conn.execute('SELECT * FROM user WHERE email = ?', (email, )).fetchall()
                conn.close()
            except Exception as e:
                conn =  get_db_connection_login()
                conn.execute(
                  'INSERT INTO user (email, password, name, admin) VALUES (?, ?, ?, ?)', 
                  (email, password, name, 'False'))
                conn.commit()
                conn.close()
            else:
                flash('Esse e-mail já está sendo utilizado!')

    user=get_username()

    return render_template('register.html', numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#PAG. ADMIN    
@app.route('/admin')
@login_required
def admin():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    return render_template('index.html', posts=posts)

#RENDERIZAR POSTS
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)

    user=get_username()

    return render_template('post.html', post=post, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#CRIAR POSTS
@app.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        try:
            title = request.form['title']
            name = request.form['name']
            content = request.form['content']
            images = request.form['images']
            date_of_birth = request.form['date_of_birth']
            if not date_of_birth:
                date_of_birth = "None"
            locate_of_birth = request.form['locate_of_birth']
            if not locate_of_birth:
                locate_of_birth = "None"
            nationality = request.form['nationality']
            if not nationality:
                nationality = "None"
            spouse = request.form['spouse']
            if not spouse:
                spouse = "None" 
            affiliations = request.form['affiliations']
            if not affiliations:
                affiliations = "None" 
            occupation = request.form['occupation']
            if not occupation:
                occupation = "None" 
            partner = request.form['partner']
            if not partner:
                partner = "None" 
            mother = request.form['mother']
            if not mother:
                mother = "None" 
            father = request.form['father']
            if not father:
                father = "None" 
            knows_as = request.form['knows_as']
            if not knows_as:
                knows_as = "None" 
            kinship = request.form['kinship']
            if not kinship:
                kinship = "None" 
            date_of_death = request.form['date_of_death']
            if not date_of_death:
                date_of_death = "None" 
            locate_of_death = request.form['locate_of_death']
            if not locate_of_death:
                locate_of_death = "None" 
            genre = request.form['genre']
            if not genre:
                genre = "None" 
            years_active = request.form['years_active']
            if not years_active:
                years_active = "None" 
            label = request.form['label']
            if not label:
                label = "None" 
            website = request.form['website']
            if not website:
                website = "None" 
            members = request.form['members']
            if not members:
                members = "None" 
        except Exception as e:
            print(e)
        else:
            if not title:
                flash('O titulo da postagem é requirido.')
            elif not name:
                flash('O nome da postagem é requirido.')
            elif not content:
                flash('O conteúdo da postagem é requirido.')
            elif not images:
                flash('A imagem da postagem é requirido.')
            else:
                conn = get_db_connection()
                conn.execute(
                    'INSERT INTO posts (title, name, content, images, date_of_birth, locate_of_birth, nationality, spouse, affiliations, occupation, partner, mother, father, knows_as, kinship, date_of_death, locate_of_death, genre, years_active, label, website, members) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (title, name, content, images, date_of_birth, locate_of_birth,
                    nationality, spouse, affiliations, occupation, partner,
                    mother, father, knows_as, kinship, date_of_death,
                    locate_of_death, genre, years_active, label, website, members))
                conn.commit()
                conn.close()
                
                return redirect('/admin')

    return render_template('create.html')

#EDITAR POSTS
@app.route('/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    post = get_post(id)
    if request.method == 'POST':
        try:
            title = request.form['title']
            name = request.form['name']
            content = request.form['content']
            images = request.form['images']
            date_of_birth = request.form['date_of_birth']
            locate_of_birth = request.form['locate_of_birth']
            nationality = request.form['nationality']
            spouse = request.form['spouse']
            if spouse == None:
                spouse = "None" 
            affiliations = request.form['affiliations']
            if affiliations == None:
                affiliations = "None" 
            occupation = request.form['occupation']
            if occupation == None:
                occupation = "None" 
            partner = request.form['partner']
            if partner == None:
                partner = "None" 
            mother = request.form['mother']
            if mother == None:
                mother = "None" 
            father = request.form['father']
            if father == None:
                father = "None" 
            knows_as = request.form['knows_as']
            if knows_as == None:
                knows_as = "None" 
            kinship = request.form['kinship']
            if kinship == None:
                kinship = "None" 
            date_of_death = request.form['date_of_death']
            if date_of_death == None:
                date_of_death = "None" 
            locate_of_death = request.form['locate_of_death']
            if locate_of_death == None:
                locate_of_death = "None" 
            genre = request.form['genre']
            if genre == None:
                genre = "None" 
            years_active = request.form['years_active']
            if years_active == None:
                years_active = "None" 
            label = request.form['label']
            if label == None:
                label = "None" 
            website = request.form['website']
            if website == None:
                website = "None" 
            members = request.form['members']
            if members == None:
                members = "None" 
        except Exception as e:
            print(e)
        else:
            conn = get_db_connection()
            conn.execute(
                'UPDATE posts SET title = ?, name = ?, content = ?, images = ?, date_of_birth = ?, locate_of_birth = ?, nationality = ?, spouse = ?, affiliations = ?, occupation = ?, partner = ?, mother = ?, father = ?, knows_as = ?, kinship = ?, date_of_death = ?, locate_of_death = ?, genre = ?, years_active = ?, label = ?, website = ?, members = ?'
                ' WHERE id = ?',
                (title, name, content, images, date_of_birth, locate_of_birth, nationality, spouse, affiliations, occupation, partner, mother, father, knows_as, kinship, date_of_death, locate_of_death, genre, years_active, label, website, members, id))
            conn.commit()
            conn.close()
            return redirect('/admin')

    return render_template('edit.html', post=post)

#DELETAR POSTS
@app.route('/<int:id>/delete', methods=('POST', ))
@login_required
def delete(id):
    post = get_post(id)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (id, ))
    conn.commit()
    conn.close()

    return redirect('/admin')

#PAG. ARTIGOS (mostrar em órdem alfabética)
@app.route('/artigos')
def artigos():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY title ASC').fetchall()
    conn.close()

    user = get_username()

    return render_template('artigos.html', posts=posts, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#PESQUISAR
@app.route('/search', methods=('GET', 'POST'))
def search():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    postagem = {}
    if request.method == "POST":    
        try:
            search = request.form['search']
            for post in posts:
                if search.upper()[0] in post['title'][0]:
                    posts_search = post['title']
                    postagem[post['id']] = post['title']
        except Exception as e:
            pass

    user = get_username()

    return render_template('artigos-search.html', postagem=postagem, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

#
#
# USUÁRIOS
#
#

#VER TODOS OS USUÁRIOS
@app.route('/users')
@login_required
def users():
    conn = get_db_connection_login()
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('users.html', users=users)

#EDITAR USUÁRIO
@app.route('/user/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def user_edit(id):
    user = get_user(id)
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            name = request.form['name']
        except Exception as e:
            print(e)
        else:
            if not password:
                conn = get_db_connection_login()
                conn.execute(
                    'UPDATE user SET email = ?, name = ?'
                    ' WHERE id = ?',
                    (email, name, id))
                conn.commit()
                conn.close()
                return redirect('/users')
            else:
                conn = get_db_connection_login()
                conn.execute(
                    'UPDATE user SET email = ?, password = ?, name = ?'
                    ' WHERE id = ?',
                    (email, password, name, id))
                conn.commit()
                conn.close()
                return redirect('/users')

    return render_template('user-edit.html', user=user)

#DELETAR USUÁRIO
@app.route('/user/<int:id>/delete', methods=('POST', ))
@login_required
def user_delete(id):
    post = get_user(id)
    conn = get_db_connection_login()
    conn.execute('DELETE FROM user WHERE id = ?', (id, ))
    conn.commit()
    conn.close()

    return redirect('/users')

#PÁG. DE USUÁRIO
@app.route('/user/<int:user_id>')
def profile(user_id):
    user1 = get_user(user_id)

    user2=get_username()

    return render_template('profile.html', post=post, numero_de_posts=number_of_posts(), user=user2[0], gravatar=gravatar(user2[1]), users = user1, id=user2[2], gravatar2=gravatar2(user1['email']))

#EDITAR USUÁRIO
@app.route('/user/edit/', methods=('GET', 'POST'))
def user_edit_main():
    user=get_username()

    if user[0] == 'visitante':
        return redirect("/")
        flash('Você precisar entrar em uma conta para editar algo.')
    else:
        if request.method == 'POST':
            try:
                profile = request.form['profile']
                name = request.form['name']
            except Exception as e:
                print(e)
            else:
                conn = get_db_connection_login()
                conn.execute(
                    'UPDATE user SET profile = ?, name = ?'
                    ' WHERE id = ?',
                    (profile, name, user[2]))
                conn.commit()
                conn.close()

                return redirect(f'/user/{user[2]}')
                flash('Informações de usuário atualizadas com sucesso')

    return render_template('user-edit-main.html', user=user[0], gravatar=gravatar(user[1]), id=user[2], profile=user[3])

app.run("0.0.0.0", 8080)
