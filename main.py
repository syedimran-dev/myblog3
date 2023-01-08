from datetime import date
from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, check_password_hash

from form import RegisterForm, LoginForm, PostForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
ckeditor = CKEditor(app)
Bootstrap5(app)

# configure db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///self_blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)




@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Tables


class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="author")

    def __init__(self, name, email, password):
        self.name = name
        self.email = email
        self.password = password


class BlogPost(db.Model):
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="parent_posts")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key="True")
    comment = db.Column(db.String(255), nullable=False)
    author = relationship("User", back_populates="comments")
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    parent_posts = relationship("BlogPost", back_populates="comments")
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))


with app.app_context():
    db.create_all()


@app.route('/', methods=["POST", "GET"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form, current_user=current_user)


@app.route('/register', methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        password_hash = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8)
        if User.query.filter_by(email=email).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for("login"))
        new_user = User(name=name, email=email, password=password_hash)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("home"))
    return render_template("register.html", form=form, current_user=current_user)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/home')
def home():
    posts = BlogPost.query.all()
    return render_template('index.html', posts=posts, current_user=current_user)


@app.route('/add_post', methods=["POST", "GET"])
@login_required
def add_post():
    form = PostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
        title = form.title.data,
        subtitle = form.subtitle.data,
        img_url = form.img_url.data,
        body= form.body.data,
        author = current_user,
        date = date.today().strftime("%B %d %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect('home')
    return render_template('add_post.html', form=form, current_user=current_user)


@app.route('/post/<int:post_id>', methods=["POST", "GET"])
def show_post(post_id):
    form = CommentForm()
    post = BlogPost.query.get(post_id)
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash("You need to login or register to comment.")
            return redirect(url_for("login"))
        new_comment = Comment(comment=form.comment_text.data, author=current_user, parent_posts=post)
        db.session.add(new_comment)
        db.session.commit()
    return render_template('post.html', post=post, current_user=current_user, form=form)


@app.route('/edit/<int:post_id>', methods=["POST", "GET"])
@login_required
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = PostForm(
        title = post.title,
        subtitle = post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.img_url = edit_form.img_url.data
        post.body = edit_form.body.data
        db.session.commit()
        return redirect(url_for('show_post', post_id=post.id))
    return render_template('add_post.html', is_edit=True, current_user=current_user, form=edit_form)


@app.route('/delete/<int:post_id>')
@login_required
def delete(post_id):
    delete_post = BlogPost.query.get(post_id)
    db.session.delete(delete_post)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)

