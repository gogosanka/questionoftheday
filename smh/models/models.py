from smh import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask.ext.login import UserMixin
from smh import lm
from smh.blogic import *#imports depend on where you're importing from, specifically if it's from the app or within another folder
from hashlib import md5

@lm.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

'''the db.Model class has a all() method which queries the db
   and returns all the db rows created. For example,
   users = User.query.get(1) #returns the 1st user object
   users.posts.all() #will return all the posts associated with user 1
   the Post class is defined below, and has a relationship within
   the User class, which is why this works.'''

followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

vibes = db.Table('vibes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('vibe_id', db.Integer, db.ForeignKey('vibe.id'))
)

vibes_accepted = db.Table('vibes_accepted',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('vibe_id', db.Integer, db.ForeignKey('vibe.id'))
)

messages = db.Table('messages',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('message_id', db.Integer, db.ForeignKey('message.id'))
)

tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')),
    db.Column('post_id', db.Integer, db.ForeignKey('post.id'))
)

question_tags = db.Table('question_tags',
    db.Column('question_tag_id', db.Integer, db.ForeignKey('question_tag.id')),
    db.Column('question_id', db.Integer, db.ForeignKey('question.id'))
) 

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(32), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    post = db.relationship('Post', backref='author', lazy='dynamic')
    question = db.relationship('Question', backref='author', lazy='dynamic')
    album = db.relationship('Album', backref='author', lazy='dynamic')
    images = db.relationship('Image', backref='author', lazy='dynamic')
    cover = db.relationship('Cover', backref='author', lazy='dynamic')
    vibes_to_date = db.Column(db.Integer)
    catchphrase = db.Column(db.String(32))
    created = db.Column(db.DateTime)
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                                secondary=followers,
                                primaryjoin=(followers.c.follower_id == id),
                                secondaryjoin=(followers.c.followed_id == id),
                                backref=db.backref('followers', lazy='dynamic'),
                                lazy='dynamic')
    vibes = db.relationship('Vibe',
                            secondary=vibes,
                            backref=db.backref('recipients', lazy='dynamic'),
                            lazy='dynamic')
    vibes_accepted = db.relationship('Vibe',
                            secondary=vibes_accepted,
                            backref=db.backref('was_accepted_by', lazy='dynamic'),
                            lazy='dynamic')
    inbox = db.relationship('Message',
                            secondary=messages,
                            backref=db.backref('recipient_inbox', lazy='dynamic'),
                            lazy='dynamic')
    
    def followed_posts(self):
        return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc()) #read this thoroughly to understand it
    password_hash = db.Column(db.String(128))
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self,password):
        self.password_hash = generate_password_hash(password)
    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)
    def is_anonymous():
        return False
    def get_id(self):
        return (self.id)
    def __repr__(self):
        return (self.nickname)
    #handle following a user
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self
    #handle unfollowing a user
    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self
    #handle checking if a user is being followed
    def is_following(self, user):
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0
    #handle if a vibe is to be followed
    def follow_vibe(self, vibe):
        if not self.is_following_vibe(vibe):
            self.vibes.append(vibe)
            return self
    def unfollow_vibe(self, vibe):
        if self.is_following_vibe(vibe):
            self.vibes.remove(vibe)
            self.vibes_accepted.remove(vibe)
            return self
    def is_following_vibe(self, vibe):
        return self.vibes.filter(vibes.c.vibe_id == vibe.id).count() > 0
    #takes in a user so that the message shows who accepted the vibe
    def accept_vibe(self, user, vibe):
        if not self.has_accepted_vibe(vibe):
            self.vibes_accepted.append(vibe)
            blogic.push_vibe(self, creator, message, vibe)
            return self
    #alert all watchers of vibe, ie vibe followers, of updates. in other words, mass message them
    #the below code is crap. refer to accept_vibe for help
    def alert_watchers(self, user, vibe):
        if not self.has_accepted_vibe(vibe):
            creator = User.query.filter_by(nickname=vibe.created_by.nickname).first()
            #message should check if a message label is created, and return the label as a placeholder instead
            self.vibes_accepted.append(vibe)
            blogic.push_vibe(self, user, vibe)
            return self
    def has_accepted_vibe(self, vibe):
        return self.vibes.filter(vibes.c.vibe_id == vibe.id).count() > 0
    def send_message(self, message):
        self.messages.append(message)
        return self
    def push_vibes(self, vibe):
        if not self.has_accepted_vibe(vibe):
            self.vibes_accepted.append(vibe)
            blogic.push_vibe(self, vibe)
            return self
    def has_pushed_vibe(self, vibe):
        return self.vibes.filter(vibes.c.vibe_id == vibe.id).count() > 0
    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % (md5(self.email.encode('utf-8')).hexdigest(), size)

#Vibe Vibes are the easiest way for people to get in touch to do something in particular.
#user vibes are vibes that follow a user
#user vibing are vibes that the user follows
class Vibe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary)
    message = db.Column(db.String(77))
    accepted_by = db.Column(db.Boolean)
    public = db.Column(db.Boolean)
    private = db.Column(db.Boolean)
    created_by = db.Column(db.String(32))
    created = db.Column(db.DateTime)
    seen_timestamp = db.Column(db.DateTime)
    def __repr__(self):
        return (self.message)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    sent_by = db.Column(db.String(32))
    created_timestamp = db.Column(db.DateTime)
    seen_timestamp = db.Column(db.DateTime)
    #be cute! randomize the <says> to say other things like "vibes, explains, announces, mumbles, bellows" etc.
    #I left a placeholder for now, but try randomizing those words and replace <says> with a variable
    def __repr__(self):
        return (self.sent_by + " <says>: "+ self.message)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.LargeBinary)
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.String(500), db.ForeignKey('post.id'))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime)

class QuestionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime)

class Album(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    #create an association table for the many-to-many relationship

class Cover(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cover = db.Column(db.LargeBinary, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rebin = db.Column(db.String(5))
    public = db.Column(db.String(8))
    body = db.Column(db.String(500))
    title = db.Column(db.String(32))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    album_id = db.Column(db.Integer, db.ForeignKey('album.id'))
    tags = db.relationship('Tag', secondary = tags, backref=db.backref('posts', lazy='dynamic'))
    image = db.relationship('Image', backref='post', lazy='dynamic')
    rating = db.Column(db.Boolean)
    def hide(self):
        self.public = 'false'
        db.session.commit()
    def unhide(self):
        self.public = 'true'
        db.session.commit()
    def __repr__(self):
        repre = "%r" % self.body
        return str(repre)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    approved = db.Column(db.String(5))
    body = db.Column(db.String(500))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    question_tags = db.relationship('QuestionTag', secondary = question_tags, backref=db.backref('questions', lazy='dynamic'))
    def hide(self):
        self.approved = 'false'
        db.session.commit()
    def unhide(self):
        self.approved = 'true'
        db.session.commit()
    def __repr__(self):
        repre = "%r" % self.body
        return str(repre)