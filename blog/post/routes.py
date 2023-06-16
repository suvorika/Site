from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from blog import db
from blog.models import Comment, Post
from blog.post.forms import PostForm, PostUpdateForm
from blog.user.forms import AddCommentForm
from blog.user.utils import save_picture_post

posts = Blueprint("post", __name__, template_folder="templates")


@posts.route("/post/new", methods=["GET", "POST"])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            image_post=form.picture.data,
            author=current_user,
        )
        picture_file = save_picture_post(form.picture.data)
        post.image_post = picture_file
        db.session.add(post)
        db.session.commit()

        flash("Пост был опубликован!", "success")
        return redirect(url_for("main.blog"))
    image_file = url_for(
        "static",
        filename=f"profile_pics/"
        + current_user.username
        + "/post_images/"
        + current_user.image_file,
    )
    return render_template(
        "post/create_post.html",
        title="Новая статья",
        form=form,
        legend="Новая статья",
        image_file=image_file,
    )


@posts.route("/post/<int:post_id>", methods=["GET", "POST"])
@login_required
def post(post_id):
    post = Post.query.get_or_404(post_id)
    comment = (
        Comment.query.filter_by(post_id=post.id)
        .order_by(db.desc(Comment.date_posted))
        .all()
    )
    post.views += 1
    db.session.commit()
    form = AddCommentForm()
    if request.method == "POST":
        if form.validate_on_submit():
            username = current_user.username
            comment = Comment(username=username, body=form.body.data, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
            flash("Комментарий к посту был добавлен", "success")
            return redirect(url_for("post.post", post_id=post_id))
    image_file = url_for(
        "static",
        filename=f"profile_pics/"
        + "users/"
        + post.author.username
        + "/post_images/"
        + post.image_post,
    )
    return render_template(
        "post/post.html",
        title=post.title,
        post=post,
        image_file=image_file,
        post_id=post_id,
        form=form,
        comment=comment,
    )


@posts.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)

    if post.author != current_user:
        abort(403)
    form = PostUpdateForm()
    if request.method == "GET":
        form.title.data = post.title
        form.content.data = post.content

    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        if form.picture.data:
            post.image_post = save_picture_post(form.picture.data)
        db.session.commit()
        flash("Данный пост был обновлён", "success")

        return redirect(url_for("post.post", post_id=post.id))

    image_file = url_for(
        "static",
        filename=f"profile_pics/{current_user.username}/post_images/{post.image_post}",
    )

    return render_template(
        "post/update_post.html",
        title="Обновить статью",
        form=form,
        legend="Обновить статью",
        image_file=image_file,
        post=post,
    )


@posts.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash("Данный пост был удален", "success")
    return redirect(url_for("user.account"))
