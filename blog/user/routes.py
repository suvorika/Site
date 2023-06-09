import os
import shutil
from datetime import datetime

from flask import Blueprint, render_template, flash, request, url_for
from flask_login import current_user, logout_user, login_required, login_user
from werkzeug.utils import redirect

from blog import bcrypt, db
from blog.models import Post, User
from blog.user.forms import LoginForm, RegistrationForm, UpdateAccountForm
from blog.user.utils import save_picture

users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.blog"))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

        full_path = os.path.join(
            os.getcwd(), "blog/static", "profile_pics", user.username
        )
        if not os.path.exists(full_path):
            os.mkdir(full_path)
        shutil.copy(f"{os.getcwd()}/blog/static/profile_pics/default.jpg", full_path)
        flash("Ваш аккаунт был создан. Вы можете войти на блог", "success")
        return redirect(url_for("users.login"))
    return render_template(
        "register.html", form=form, title="Регистрация", legend="Регистрация"
    )


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.blog"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get("next")
            flash("Вы вошли как пользователь {current_user.username}", "info")
            return (
                redirect(next_page) if next_page else redirect(url_for("users.account"))
            )
        else:
            flash(
                "Войти не удалось. Пожалуйста, првоерьте электронную почту или пароль",
                "danger",
            )
    return render_template("login.html", form=form, title="Логин", legend="Войти")


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    user = User.query.filter_by(username=current_user.username).first()
    posts = Post.query.all()
    users = User.query.all()
    form = UpdateAccountForm()

    if request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email
    elif form.validate_on_submit():
        path_one = os.path.join(os.getcwd(), f'blog/static/profile_pics/{user.username}')
        path_two = os.path.join(os.getcwd(), f'blog/static/profile_pics/{form.username.data}')
        os.rename(path_one, path_two)
        current_user.username = form.username.data
        current_user.email = form.email.data

        if form.picture.data:
            current_user.image_file = save_picture(form.picture.data)
        else:
            form.picture.data = current_user.image_file

        db.session.commit()
        flash("Ваш аккаунт был обновлён!", "success")
        return redirect(url_for("user.account"))
    image_file = url_for(
        "static",
        filename=f"profile_pics/"
        + current_user.username
        + "/account_image/"
        + current_user.image_file,
    )
    return render_template(
        "account.html",
        tittle="Аккаунт",
        users=users,
        posts=posts,
        user=user,
        image_file=image_file,
        form=form,
    )


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = (
        Post.query.filter_by(author=user)
        .order_by(Post.date_posted.desc())
        .paginate(page=page, per_page=3)
    )

    return render_template(
        "user/user_posts.html", title="Блог>", posts=posts, user=user
    )


@users.route("/logout")
@login_required
def logout():
    current_user.last_seen = datetime.now()
    db.session.commit()
    logout_user()
    return redirect(url_for("main.home"))
