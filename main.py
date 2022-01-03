import sqlite3
from flask import Flask, Blueprint, render_template, request, url_for, flash, redirect, jsonify
from werkzeug.exceptions import abort
import functools
from time import sleep
import uuid, time
from random import randint, choice
from libgravatar import Gravatar 
from discord_webhook import DiscordWebhook, DiscordEmbed

app = Flask(__name__)

app.secret_key = '...'
ips = {}
number_list = {
  "1": "a",
  "2": "b",
  "3": "c",
  "4": "d",
  "5": "e",
  "6": "f",
  "7": "g",
  "8": "h",
  "9": "i",
  "10": "j",
  "11": "k",
  "12": "l",
  "13": "m",
  "14": "n",
  "15": "o",
  "16": "p",
  "17": "q",
  "18": "r",
  "19": "s",
  "20": "t",
  "21": "u",
  "22": "v",
  "23": "w",
  "24": "x",
  "25": "y",
  "26": "z",
}

def new_article(name):
    webhook = DiscordWebhook(url='...')
    name_url = name.replace(' ', '%20')
    embed = DiscordEmbed(title=f'EARTHPEDIA - AVISOS', description=f'O artigo {name} acabou de ser criado, clique [https://earthpedia.com.br/{name_url}](aqui) para dar uma olhadinha no mesmo!', color='0000ff')
    embed.set_timestamp()

    webhook.add_embed(embed)

    response = webhook.execute()

def gravatar(mail, type=None):
    if type == None:
        try:
            g = Gravatar(mail)
            return g.get_image()
        except:
            pass
    elif type == "500x500":
        try:
            g = Gravatar(mail)
            return g.get_image(size=500)
        except:
            pass

def get_db_connection(type=None):
    if type == None:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    elif type == "user":
        conn = sqlite3.connect('user/database.db')
        conn.row_factory = sqlite3.Row
        return conn
    elif type == "ip":
        conn = sqlite3.connect('ips/database.db')
        conn.row_factory = sqlite3.Row
        return conn

def get_db_informations(type, args=None, id=None):
    if type == "post":
        if id == True:
            conn = get_db_connection()
            post = conn.execute('SELECT * FROM posts WHERE id = ?',
                            (args, )).fetchone()
            conn.close()
            if post is None:
                abort(404)
            return post
        else:
            conn = get_db_connection()
            post = conn.execute('SELECT * FROM posts WHERE title = ?',
                            (args, )).fetchone()
            conn.close()
            if post is None:
                abort(404)
            return post
    if type == "user":
        conn = get_db_connection("user")
        user = conn.execute('SELECT * FROM user WHERE id = ?',
                          (args, )).fetchone()
        conn.close()
        if post is None:
            abort(404)
        return user
    if type == "username":
        try:
            yip = request.headers.get('X-Forwarded-For', request.remote_addr)
            conn = get_db_connection("ip")
            logins = conn.execute('SELECT * FROM logins').fetchall()
            conn.close()
            list_of_ips = {}
            for login in logins:
                list_of_ips[login['ip']] = login['id']
            id = list_of_ips[yip]
            conn = get_db_connection("user")
            user = conn.execute('SELECT * FROM user WHERE id = ?', (id, )).fetchone()
            conn.close()

            if user['profile'] == None:
                lista = [user['name'], user['email'], id, '...']
            else:
                lista = [user['name'], user['email'], id, user['profile']]

            return lista
        except:
            lista = ['visitante', 'None', 'None', '...']
            return lista

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        conn = get_db_connection("ip")
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

def number_of_posts():
    number_of_posts = 0

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    for post in posts:
        number_of_posts += 1

    return number_of_posts

def posts_sort():
    all_ids = []
    list_of_ids = []
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()
    for post in posts:
        all_ids.append(post['id'])
    while True:
        if len(list_of_ids) < 5:
            number = choice(all_ids)
            if number in list_of_ids:
                pass
            else:
                list_of_ids.append(number)
        else:
            break

    posts_list = []

    for ids in list_of_ids:
        post = get_db_informations("post", ids, True)
        posts_list.append(post)

    return posts_list

@app.route('/')
def index():
    user = get_db_informations("username")

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    conn = get_db_connection("user")
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('app.html', posts=posts, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2], posts_sort=posts_sort())

@app.route('/login', methods=('GET', 'POST'))
def login():
    yip = request.headers.get('X-Forwarded-For', request.remote_addr)
    conn = get_db_connection("ip")
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
        conn =  get_db_connection("user")
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
                        conn = get_db_connection("ip")
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

    user = get_db_informations("username")

    return render_template('login.html', numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

@app.route('/logout', methods=('GET', 'POST'))
def logout():
    try:
        yip = request.headers.get('X-Forwarded-For', request.remote_addr)
        conn = get_db_connection("ip")
        conn.execute('DELETE FROM logins WHERE ip = ?', (yip, ))
        conn.commit()
        conn.close()

        del ips[request.headers.get('X-Forwarded-For', request.remote_addr)]

        return redirect("/")
    except:
        return redirect("/")
        pass

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
                conn =  get_db_connection("login")
                users = conn.execute('SELECT * FROM user WHERE email = ?', (email, )).fetchall()
                conn.close()
            except Exception as e:
                conn =  get_db_connection("login")
                conn.execute(
                  'INSERT INTO user (email, password, name, admin) VALUES (?, ?, ?, ?)', 
                  (email, password, name, 'False'))
                conn.commit()
                conn.close()
            else:
                flash('Esse e-mail já está sendo utilizado!')

    user = get_db_informations("username")

    return render_template('register.html', numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

@app.route('/admin')
@login_required
def admin():
    user = get_db_informations("username")

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    conn = get_db_connection("user")
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('index.html', posts=posts, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2], posts_sort=posts_sort())

@app.route('/<post_name>')
def post(post_name):
    post = get_db_informations("post", post_name)

    user = get_db_informations("username")

    return render_template('post.html', post=post, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2])

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
            try:
                new_article(title)
            except:
                pass
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

    user = get_db_informations("username")

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    conn = get_db_connection("user")
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('create.html', numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2], posts_sort=posts_sort())

@app.route('/<post_name>/edit', methods=('GET', 'POST'))
@login_required
def edit(post_name):
    post = get_db_informations("post", post_name)
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
                ' WHERE title = ?',
                (title, name, content, images, date_of_birth, locate_of_birth, nationality, spouse, affiliations, occupation, partner, mother, father, knows_as, kinship, date_of_death, locate_of_death, genre, years_active, label, website, members, post_name))
            conn.commit()
            conn.close()
            return redirect('/admin')
                
    user = get_db_informations("username")

    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts').fetchall()
    conn.close()

    conn = get_db_connection("user")
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('edit.html', post=post, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2], posts_sort=posts_sort())

@app.route('/<post_name>/delete', methods=('POST', ))
@login_required
def delete(post_name):
    post = get_db_informations("post", post_name)
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE title = ?', (post_name, ))
    conn.commit()
    conn.close()

    return redirect('/admin')

@app.route('/artigos')
def artigos():
    conn = get_db_connection()
    posts = conn.execute('SELECT * FROM posts ORDER BY title ASC').fetchall()
    conn.close()

    user = get_db_informations("username")

    return render_template('artigos.html', posts=posts, numero_de_posts=number_of_posts(), user=user[0], gravatar=gravatar(user[1]), id=user[2], number_list=number_list)

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

    user = get_db_informations("username")

    return render_template('artigos-search.html', postagem=postagem, user=user[0], gravatar=gravatar(user[1]), id=user[2])

@app.route('/users')
@login_required
def users():
    conn = get_db_connection("login")
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()

    return render_template('users.html', users=users)

#EDITAR USUÁRIO
@app.route('/user/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def user_edit(id):
    user = get_db_informations("user", id)
    if request.method == 'POST':
        try:
            email = request.form['email']
            password = request.form['password']
            name = request.form['name']
        except Exception as e:
            print(e)
        else:
            if not password:
                conn = get_db_connection("login")
                conn.execute(
                    'UPDATE user SET email = ?, name = ?'
                    ' WHERE id = ?',
                    (email, name, id))
                conn.commit()
                conn.close()
                return redirect('/users')
            else:
                conn = get_db_connection("login")
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
    post = get_db_informations("user", id)
    conn = get_db_connection("login")
    conn.execute('DELETE FROM user WHERE id = ?', (id, ))
    conn.commit()
    conn.close()

    return redirect('/users')

@app.route('/user/<int:user_id>')
def profile(user_id):
    user1 = get_db_informations("user", user_id)

    user2 = get_db_informations("username")

    return render_template('profile.html', post=post, numero_de_posts=number_of_posts(), user=user2[0], gravatar=gravatar(user2[1]), users = user1, id=user2[2], gravatar2=gravatar(user1['email'], "500x500"))

@app.route('/user/edit/', methods=('GET', 'POST'))
def user_edit_main():
    user = get_db_informations("username")

    if user[0] == 'visitante':
        return redirect("/")
        flash('Você precisa entrar em uma conta para editar algo.')
    else:
        if request.method == 'POST':
            try:
                profile = request.form['profile']
                name = request.form['name']
            except Exception as e:
                print(e)
            else:
                conn = get_db_connection("user")
                conn.execute(
                    'UPDATE user SET profile = ?, name = ?'
                    ' WHERE id = ?',
                    (profile, name, user[2]))
                conn.commit()
                conn.close()

                return redirect(f'/user/{user[2]}')
                flash('Informações de usuário atualizadas com sucesso')

    return render_template('user-edit-main.html', user=user[0], gravatar=gravatar(user[1]), id=user[2], profile=user[3])

@app.route('/discord')
def discord():
  return redirect('https://discord.gg/hhwxP474wz')

app.run("0.0.0.0", 8080)