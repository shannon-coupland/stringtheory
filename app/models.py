from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import login


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

saved_patterns = db.Table('saved_patterns',
    db.Column('pattern_id', db.Integer, db.ForeignKey('pattern.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    uploaded_patterns = db.relationship('Pattern', backref='owner')
    saved_patterns = db.relationship('Pattern', secondary=saved_patterns, backref='users')

    def __repr__(self):
        return '<User: {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

tags = db.Table('tags',
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
    db.Column('pattern_id', db.Integer, db.ForeignKey('pattern.id'), primary_key=True)
)

class Pattern(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), index=True, nullable=False)
    filename = db.Column(db.String(120))
    file = db.Column(db.LargeBinary())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    comments = db.relationship('Comment', backref='pattern', lazy='dynamic')
    tags = db.relationship('Tag', secondary=tags, backref='patterns')
    image_filename = db.Column(db.String(120))
    description = db.Column(db.String(1000))

    def __repr__(self):
        return '<Pattern: {}, user: {}>'.format(self.name, self.user_id)


class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(30), index=True)

    def __repr__(self):
        return '<Tag: {}>'.format(self.label)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    pattern_id = db.Column(db.Integer, db.ForeignKey('pattern.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Comment: {}>'.format(self.body)
