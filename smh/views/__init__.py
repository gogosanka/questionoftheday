from flask import render_template, flash, redirect, session, url_for, request, abort
from flask.ext.login import login_user, logout_user, current_user, login_required
from smh import app, db, lm, blogic
from smh.forms import LoginForm, NameForm, SignupForm, AskForm, VibeMeForm
from smh.models.models import User, Post, Vibe, Question
from datetime import datetime
from smh.auth import *
import time

@app.route('/', methods=['GET'])
def questions():
    form = VibeMeForm()
    title = "Exploring Social Issues Through Anonymity"
    qotd = Question.query.filter_by(approved='true').first()
    user = "Anonymous"
    if current_user.is_authenticated():
        user = current_user.nickname
        return render_template('smh/qotd.html',
                                title=title,
                                user=user,
                                followers=followers,
                                qotd=qotd,
                                form=form) 
    return render_template('smh/qotd.html',
                                title=title,
                                questions=questions)

@app.route('/questions', methods=['GET', 'POST'])
@login_required
def send():
    body = request.form['question']
    author = request.form['author']
    if body:
        if author:
            blogic.ask(body,author,title)
            flash("created post successfully!")
            return redirect(url_for('questions', nickname=current_user.nickname))
    else:
        return render_template('404.html')

@app.route('/admin/allusers', methods=['GET'])
@login_required
def allusers():
    users = User.query.all()
    return render_template('admin/allusers.html', users=users)

@app.route('/error')
@login_required
def nopage():
    return render_template('404.html')

@app.route('/<nickname>/accept/<int:vibeid>', methods=['POST'])
@login_required
def accept_vibe(nickname, vibeid):
    vibe = Vibe.query.get(vibeid)
    user = User.query.filter_by(nickname=nickname).first()
    recipient = User.query.filter_by(nickname=current_user.nickname).first()
    if request.method == 'POST':
        if current_user.is_authenticated and current_user.nickname != nickname:
            if user:
                if vibe:
                    if vibe in current_user.vibes:
                        blogic.accept_vibe(recipient, user, vibe)
                        return render_template('profile', nickname=current_user.nickname)

@app.route('/<nickname>', methods=['GET', 'POST'])
def profile(nickname):
    form = AskForm()
    user = User.query.filter_by(nickname=current_user.nickname).first()
    if current_user.is_authenticated and nickname == current_user.nickname:
        #if the page is the current user's, load the dashboard. otherwise load the profile pages
        #this way we keep people from changing or seeing other people's information
        return render_template('smh/dashboard.html',
                                title="Dashboard",
                                user=user,
                                form=form)
    else:
        #open the generic viewing of profile pages, not the dashboard. will need to create this template and remove the "profile.html" below
        user = User.query.filter_by(nickname=nickname).first()
        form = VibeMeForm()
        if user:
            return render_template('smh/dashboard.html', title=(str(nickname) + "'s Activity"), user=user, form=form)
        else:
            flash('Could not find user %s!' % (nickname))
            return redirect(url_for('questions'))

@app.route('/update', methods=['POST'])
@login_required
def update_post():
    body = request.form['body']
    author = request.form['author']
    postid = request.form['postid']
    title = request.form['title']
    post = Post.query.get(postid)
    if post.author.nickname == current_user.nickname:
        blogic.update(body,author,postid,title)
        return redirect(url_for('posts', nickname=current_user.nickname))
    return redirect(url_for('posts', nickname=current_user.nickname))

@app.route('/edit/<int:postid>/', methods=['GET'])
@login_required
def edit(postid):
    if current_user.is_authenticated():
        user = User.query.filter_by(nickname=current_user.nickname).first()
        posts_count = Post.query.filter_by(author=user, rebin='false').count()
        post = Post.query.get(postid)
        if post:
            if post.author.nickname == current_user.nickname:
                return render_template('edit.html',
                                    title="Edit Post",
                                    user=user,
                                    post=post, #recognize that it is written singular tense here, as we are showing 1 post not multiple
                                    posts_count=posts_count,
                                    bin_posts=bin_posts,
                                    bin_count=bin_count,
                                    follower=follower)
            else:
                return redirect(url_for('posts', nickname=current_user.nickname))
        return render_template('404.html')
    else:
        return render_template('404.html')

@app.route('/show/<int:postid>/', methods=['GET'])
@login_required
def show(postid):
    feed = Post.query.filter_by(rebin='false').all()
    follower = '0 for now' #count for followers. will need to update the db model
    user = 'Stranger'
    if current_user.is_authenticated():
        user = User.query.filter_by(nickname=current_user.nickname).first()
        posts_count = Post.query.filter_by(author=user, rebin='false').count()
        bin_posts = Post.query.filter_by(author=user, rebin='true').all() #all recycled posts object        
        bin_count = Post.query.filter_by(author=user, rebin='true').count() #recycled posts count
        post = Post.query.get(postid)
        if post:
            return render_template('show.html',
                                    title="View Post",
                                    user=user,
                                    post=post, #recognize that it is written singular tense here, as we are showing 1 post not multiple
                                    posts_count=posts_count,
                                    bin_posts=bin_posts,
                                    bin_count=bin_count,
                                    follower=follower)
    else:
        return render_template('404.html')

@app.route('/delete/<vibeid>/', methods=['GET'])
@login_required
def delete_vibe(vibeid):
    vibe = Vibe.query.filter_by(id=vibeid).first()
    if vibe:
        if current_user.is_authenticated and current_user.is_following_vibe(vibe):
            user = User.query.filter_by(nickname=current_user.nickname).first()
            blogic.delete_vibe(user, vibe)
            flash("Deleted Vibe!")
            return redirect(url_for('profile', nickname=current_user.nickname))
        else:
            return render_template('404.html')
    else:
        return render_template('404.html')


@app.route('/delete/<postid>/', methods=['GET'])
@login_required
def delete(postid):
    post = Post.query.filter_by(id=postid).first()
    if post:
        blogic.delete(post)
        flash("Deleted post!")
        return redirect(url_for('bin', nickname=current_user.nickname))
    else:
        return render_template('404.html')

@app.route('/recycle/<postid>/', methods=['GET'])
@login_required
def recycle(postid):
    post = Post.query.filter_by(id=postid).first()
    if post:
        blogic.recycle(post)
        if post.rebin == 'true':
            flash("Post was sent to recycling bin!")
            return redirect(url_for('profile', nickname=current_user.nickname))
        flash("Your post was restored!")
        return redirect(url_for('bin', nickname=current_user.nickname))
    else:
        return render_template('404.html')

@app.route('/<nickname>/bin', methods=['GET', 'POST'])
@login_required
def bin(nickname=current_user):
    feed = Post.query.filter_by(rebin='false').all()
    follower = '0 for now' #count for followers. will need to update the db model
    user = 'Stranger'
    if current_user.is_authenticated():
        user = User.query.filter_by(nickname=current_user.nickname).first()
        posts = Post.query.filter_by(author=user).all()
        posts_count = Post.query.filter_by(author=user, rebin='false').count()
        bin_posts = Post.query.filter_by(author=user, rebin='true').all() #all recycled posts object        
        bin_count = Post.query.filter_by(author=user, rebin='true').count() #recycled posts count
        #hidden_posts = Post.query.filter_by(author=user, rebin='false', hidden='true').all() #make sure to change blogic so that when hidden items are deleted their status goes back to visible
        return render_template('bin.html',
                                title="Recycling Bin",
                                user=user,
                                post=posts,
                                posts_count=posts_count,
                                bin_posts=bin_posts,
                                bin_count=bin_count,
                                follower=follower,
                                feed=feed)
    return render_template('auth/login.html',
                            title="Discover",
                            feed=feed,
                            user=user,
                            follower=follower)

@app.route('/visible/<postid>/', methods=['GET'])
@login_required
def visible(postid):
    post = Post.query.filter_by(id=postid).first()
    if post:
        if post.public == 'true':
            post.hide()
            flash("Vibe was hidden.")
            return redirect(url_for('profile', nickname=current_user.nickname))
        post.unhide()
        flash("Now sharing vibe.")
        return redirect(url_for('profile', nickname=current_user.nickname))
    else:
        return render_template('404.html')

@app.route('/create', methods=['POST'])
@login_required
def create():
    user = User.query.filter_by(nickname=current_user.nickname).first()
    post = request.form['body']
    author = request.form['author']
    title = request.form['title']
    if post:
        if author:
            blogic.new(post,author,title)
            flash("created post successfully!")
            return redirect(url_for('posts', nickname=current_user.nickname))
    else:
        return render_template('404.html')

@app.route('/nopage')
def no_page():
    return render_template('404.html')

@app.route('/<nickname>/posts/new')
@login_required
def new(nickname):
    feed = Post.query.filter_by(rebin='false').all()
    follower = '0 for now' #count for followers. will need to update the db model
    user = 'Stranger'
    if current_user.is_authenticated():
        user = User.query.filter_by(nickname=current_user.nickname).first()
        posts = Post.query.filter_by(author=user).all()
        posts_count = Post.query.filter_by(author=user, rebin='false').count()
        bin_posts = Post.query.filter_by(author=user, rebin='true').all() #all recycled posts object        
        bin_count = Post.query.filter_by(author=user, rebin='true').count() #recycled posts count
        #hidden_posts = Post.query.filter_by(author=user, rebin='false', hidden='true').all() #make sure to change blogic so that when hidden items are deleted their status goes back to visible
        return render_template('create.html',
                                title="Discover",
                                user=user,
                                posts_count=posts_count,
                                bin_posts=bin_posts,
                                bin_count=bin_count,
                                follower=follower,
                                feed=feed)
    return render_template('posts.html',
                            title="New Post",
                            user=user,
                            follower=follower)

@app.route('/', methods=['GET'])
@app.route('/discover', methods=['GET'])
def discover():
    feed = Post.query.filter_by(rebin='false', public='true').all()
    follower = '0 for now' #count for followers. will need to update the db model
    user = 'Stranger'
    if current_user.is_authenticated():
        user = User.query.filter_by(nickname=current_user.nickname).first()
        posts = Post.query.filter_by(author=user).all()
        posts_count = Post.query.filter_by(author=user, rebin='false').count()
        bin_posts = Post.query.filter_by(author=user, rebin='true').all() #all recycled posts object        
        bin_count = Post.query.filter_by(author=user, rebin='true').count() #recycled posts count
        #hidden_posts = Post.query.filter_by(author=user, rebin='false', hidden='true').all() #make sure to change blogic so that when hidden items are deleted their status goes back to visible
        return render_template('home.html',
                                title="Discover",
                                user=user,
                                posts_count=posts_count,
                                bin_posts=bin_posts,
                                bin_count=bin_count,
                                follower=follower,
                                feed=feed)
    return render_template('home.html',
                            title="Discover",
                            feed=feed,
                            user=user,
                            follower=follower)

@app.route('/login', methods=['GET', 'POST'])
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    user = 'Stranger'
    if form.validate_on_submit():
        user = User.query.filter_by(nickname=form.nickname.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            if request.args.get('next') is url_for('auth.login'):
                return redirect(url_for('questions'))
            return redirect(request.args.get('next') or url_for('questions'))
        flash('Invalid username or password.')
        return render_template('auth/login.html',
                                title="Log In",
                                form=form,
                                user=user)
    return render_template('auth/login.html',
                                title="Log In",
                                form=form,
                                user=user)

@auth.route('/logout')
def logout():
    try:
        logout_user()
        flash('You have been logged out.')
        return redirect(url_for('discover'))
    except:
        return redirect(url_for('discover'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    user = 'Stranger'
    created_time = datetime.utcnow()
    check_email = User.query.filter_by(email=form.email.data).first()
    check_nickname = User.query.filter_by(nickname=form.nickname.data).first()
    if form.validate_on_submit():
        if not check_email and not check_nickname:
            user = User(nickname=form.nickname.data, created=created_time, email=form.email.data, password=form.password.data, catchphrase=form.catchphrase.data, vibes_to_date=0)
            blogic.add_user(user)
            login_user(user, form.remember_me.data)
            flash('Account created successfully!')
            return redirect(request.args.get('next') or url_for('discover'))
        flash('Username or password is already taken. If this is you please sign in.')
    return render_template('signup.html',
                                title="Log In",
                                form=form,
                                user=user)

@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
    #user is the db object of the nickname argument
    user = User.query.filter_by(nickname=nickname).first()
    #current is the db object of the current logged in user
    current = User.query.filter_by(nickname=current_user.nickname).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('discover'))
    #check if the current logged in user is the same as the one we are trying to follow
    if user.id == current_user.id:
        flash('You can\'t follow yourself!')
        return redirect(url_for('profile', nickname=nickname))
    #otherwise, let's follow the user!
    u = current.follow(user)
    if u is None:
        flash('Already following ' + nickname + '.')
        return redirect(url_for('profile', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You are now following ' + nickname + '!')
    return redirect(url_for('profile', nickname=nickname))

@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
    user = User.query.filter_by(nickname=nickname).first()
    #current is the db object of the current logged in user
    current = User.query.filter_by(id=current_user.id).first()
    if user is None:
        flash('User %s not found.' % nickname)
        return redirect(url_for('discover'))
    if user.id == current_user.id:
        flash('You can\'t unfollow yourself!')
        return redirect(url_for('profile', nickname=nickname))
    u = current.unfollow(user)
    if u is None:
        flash('You are not following ' + nickname + '.')
        return redirect(url_for('profile', nickname=nickname))
    db.session.add(u)
    db.session.commit()
    flash('You have stopped following ' + nickname + '.')
    return redirect(url_for('profile', nickname=nickname))

if __name__ == '__main__':
    app.run()