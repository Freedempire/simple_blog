from datetime import date
from functools import wraps

from flask import Flask, render_template, redirect, url_for, flash, abort, request
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_bootstrap import Bootstrap5
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, URL
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor, CKEditorField
from sqlalchemy.orm import relationship
from flask_gravatar import Gravatar


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log in')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Sign up')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    subtitle = StringField('Subtitle', validators=[DataRequired()])
    img_url = StringField('Image URL', validators=[DataRequired(), URL()])
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField('Post')


class CommentForm(FlaskForm):
    body = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit')


# create admin_only decorator
def admin_only(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_user.id == 1:
            return func(*args, **kwargs)
        else:
            return abort(403)
    return wrapper


app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')

Bootstrap5(app)
ckeditor = CKEditor(app)

# configure flask-login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return db.session.get(User, int(id))


gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# configure flask-sqlalchemy
db = SQLAlchemy(app)


# configure tables
class BlogPost(db.Model):
    # __tablename__ = 'blog_post'
    id = db.Column(db.Integer, primary_key=True)
    # author = db.Column(db.String(250), nullable=False)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', back_populates='posts')
    comments = relationship('Comment', back_populates='blog_post')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), nullable=False)
    password = db.Column(db.String(250), nullable=False)
    name = db.Column(db.String(250), nullable=False)
    posts = relationship('BlogPost', back_populates='author')
    comments = relationship('Comment', back_populates='author')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(500), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = relationship('User', back_populates='comments')
    blog_post_id = db.Column(db.Integer, db.ForeignKey('blog_post.id'))
    blog_post = relationship('BlogPost', back_populates='comments')


with app.app_context():
    # create tables if not exist
    db.create_all()


@app.route('/')
def get_all_posts():
    # posts = BlogPost.query.all()
    posts = db.session.execute(db.select(BlogPost).order_by(BlogPost.date.desc())).scalars().all()
    return render_template('index.html', posts=posts)


@app.route('/post/<int:post_id>', methods=['GET', 'POST'])
def show_post(post_id):
    # post = BlogPost.query.get(post_id)
    if request.method == 'POST':
        return redirect(url_for('add_comment', post_id=post_id), code=307)
    post = db.get_or_404(BlogPost, post_id)
    comment_form = CommentForm()
    comments = db.session.execute(db.select(Comment).filter_by(blog_post_id=post_id)).scalars().all()
    return render_template('post.html', post=post, form=comment_form, comments=comments)


@app.route('/welcome')
@login_required
def welcome():
    return render_template('welcome.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        form.email.data = form.email.data.lower()
        # check email in database
        if db.session.execute(db.select(User).filter_by(email=form.email.data)).scalar():
            flash('This email has already been registered.', 'error')
            form.email.data = ''
            return render_template('register.html', form=form)
        else:
            user = User(
                email=form.email.data.lower(),
                password=generate_password_hash(form.password.data, 'scrypt'),
                name=form.name.data.title()
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('welcome'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        # validate email and password
        user = db.session.execute(db.select(User).filter_by(email=form.email.data.lower())).scalar()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('welcome'))
        else:
            flash('Email or password is incorrect.', 'warning')
            form.email.data = ''
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


@app.route('/add-new-post', methods=['GET', 'POST'])
@admin_only
def add_new_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=form.body.data,
            img_url=form.img_url.data,
            # author=current_user.name,
            author_id=current_user.id,
            date=date.today().strftime('%B %d, %Y')
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('show_post', post_id=new_post.id))
    return render_template('make_post.html', form=form)


@app.route('/edit-post/<int:post_id>', methods=['GET', 'POST'])
@admin_only
def edit_post(post_id):
    # post = BlogPost.query.get(post_id)
    post = db.get_or_404(BlogPost, post_id)
    form = PostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        body=post.body
    )
    if form.validate_on_submit():
        post.title = form.title.data
        post.subtitle = form.subtitle.data
        post.img_url = form.img_url.data
        post.body = form.body.data
        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('make_post.html', form=form, post_id=post_id)


@app.route('/delete-post/<int:post_id>')
@admin_only
def delete_post(post_id):
    # post = BlogPost.query.get(post_id)
    post = db.get_or_404(BlogPost, post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('get_all_posts'))


@app.route('/add-comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if not current_user.is_authenticated:
        flash('Get logged in before comment.', 'info')
    else:
        form = CommentForm()
        if form.validate_on_submit():
            comment = Comment(
                body=form.body.data,
                date=date.today().strftime('%B %d, %Y'),
                author_id=current_user.id,
                blog_post_id=post_id
            )
            db.session.add(comment)
            db.session.commit()
        else:
            flash('You haven\'t comment anything yet.', 'warning')
    return redirect(url_for('show_post', post_id=post_id))


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5000)
    app.run()
