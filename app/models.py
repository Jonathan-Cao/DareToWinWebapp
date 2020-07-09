from datetime import datetime
from time import time
import jwt
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

#Many-to-many relationship association table, a user follows many users, a user has many followers
followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    upvotes = db.Column(db.Integer, default=0)
    
    demerits = db.Column(db.Integer, default=0)

    badge = db.Column(db.String, default='Rookie')
    banned = db.Column(db.Integer, default=0)
    #One-to-many relationship, a user has many posts
    votes = db.relationship('Upvote', backref = 'user', lazy = 'dynamic')
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    reports = db.relationship('Report', backref='author', lazy='dynamic', foreign_keys = 'Report.reporter_id')
####    
    reports_on_me = db.relationship('Report', backref = 'user', lazy = 'dynamic',foreign_keys = 'Report.profile_id')

    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    #Users followed by this user (the follower)
    followed = db.relationship(
        'User', 
        secondary=followers, #Configures above association table
        primaryjoin=(followers.c.follower_id == id), #Follower user
        secondaryjoin=(followers.c.followed_id == id), #Followed user
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    def get_reset_password_token(self, expires_in=600): #Token expires in 10 mins
        #JWT token encoded with user id
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
            
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return None
        return User.query.get(id)
        
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)
            
    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0
    
    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            
    def own_posts(self):
        #Own posts
        own = Post.query.filter_by(user_id=self.id)
        return own.order_by(Post.timestamp.desc())
            
    def followed_posts(self):
        #Posts by followed users
        followed = Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id)
        #Own posts
        own = Post.query.filter_by(user_id=self.id)
        return followed.union(own).order_by(Post.timestamp.desc())

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dare = db.Column(db.String)#filename
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    upvotes = db.relationship('Upvote', backref='post', lazy='dynamic')
    votes = db.Column(db.Integer, default=0)
    reports = db.relationship('Report', backref='post', lazy='dynamic')
    banned = db.Column(db.Integer, default=0)
    ban_reason = db.Column(db.String(30))

    def __repr__(self):
        return '<Post {}>'.format(self.body)
        
class Upvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
####
    upvoter_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    
    def __repr__(self):
        return '<Upvote for {} by {}>'.format(self.post_id, self.upvoter_id)
        
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    reports = db.relationship('Report', backref='comment', lazy='dynamic')
    banned = db.Column(db.Integer, default=0)
    ban_reason = db.Column(db.String(30))
   
    #couldnt make this work, was trying to keep all reports, but change value to seen once action taken, but keeps giving error when i try to filter using this
    def check_existing_reports(self):
        if self.reports != None:
            for report in self.reports:
                if report.seen == 0:
                    return True
            return False
        else:
            return False

    def __repr__(self):
        return '<Comment {}>'.format(self.body)
        
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reason = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))

    ##
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    profile_id = db.Column(db.Integer, db.ForeignKey('user.id'))#rpt profile
 #   action_taken = db.Column(db.String(30))#action taken by admin
 #   seen = db.Column(db.Integer, default = 0)#shld nt delete reports
    page_of_report = db.Column(db.String(30))

    def __repr__(self):
        return 'Report by ' + str(self.author.username)   
    

