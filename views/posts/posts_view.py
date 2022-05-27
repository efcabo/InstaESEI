import flask
import flask_login
import sirope
from flask import send_file, url_for

from model.CommentDto import CommentDto
from model.PostDto import PostDto
from model.UserDto import UserDto


def get_blprint():
    posts = flask.blueprints.Blueprint("posts", __name__,
                                       url_prefix="/post",
                                       template_folder="templates",
                                       static_folder="static")
    syrp = sirope.Sirope()

    return posts, syrp


posts_blprint, srp = get_blprint()


# Permite crear una nueva publicación
@flask_login.login_required
@posts_blprint.route('new', methods=["POST", "GET"])
def new_post():
    if flask.request.method == 'POST':
        message = flask.request.form.get("edMessage")

        image = flask.request.files['file']

        if image.filename == '':
            flask.flash('Fichero no seleccionado')
            return flask.redirect(flask.request.url)

        if not message:
            flask.flash("Debes introducir un mensaje")
            return flask.redirect(flask.request.url)
        else:

            usr = UserDto.current_user()
            post = PostDto(image, message, usr.__oid__, )
            oid = srp.save(post)
            usr.add_post_oid(oid)
            srp.save(usr)

            flask.flash("Publicado correctamente")
            return flask.redirect("/user/profile")
    else:
        return flask.render_template("new_post.html")


# Genera una ruta para mostrar las imagenes de perfil
@flask_login.login_required
@posts_blprint.route('get_image/<string:post_oid>')
def get_image(post_oid):
    post = srp.load(srp.oid_from_safe(post_oid))
    image = post.image
    return send_file(image, mimetype='/image/png')


# Permite a su autor modificar un post
# Si solo se proporciona valor para uno de los campos, los cambios solo afectan a dicho campo
@flask_login.login_required
@posts_blprint.route('<string:post_oid>/modify', methods=["POST", "GET"])
def modify_post(post_oid):
    post = srp.load(srp.oid_from_safe(post_oid))

    if flask.request.method == 'POST':
        message = flask.request.form.get("edMessage")
        image = flask.request.files['file']

        if image.filename == '' and not message:
            flask.flash("Los campos están vacíos")
            return flask.redirect(flask.request.url)

        elif image.filename != '' and message:
            post.image = image
            post.msg = message
            srp.save(post)

            flask.flash("Publicación modificada correctamente")
            return flask.redirect("/user/profile")

        else:
            if image.filename != '':
                post.image = image
                srp.save(post)
                flask.flash("Se ha modificado la imagen")
                return flask.redirect("/user/profile")

            if message:
                post.msg = message
                srp.save(post)
                flask.flash("Se ha modificado el pie de página")
                return flask.redirect("/user/profile")

    else:
        sust = {
            "post": post,
            "post_oid": post_oid
        }

        return flask.render_template("modify_post.html", **sust)


# Permite, a su autor, eliminar una publicacion, eliminando también sus comentarios asociados
@flask_login.login_required
@posts_blprint.route('<string:post_oid>/delete', methods=['POST', 'GET'])
def delete_post(post_oid):
    if flask.request.method == 'POST':

        if flask.request.form.get("flexCheckDefault"):

            post_oid_fs = srp.oid_from_safe(post_oid)
            post = srp.load(post_oid_fs)

            usr = UserDto.current_user()
            usr.delete_post_oid(post_oid_fs)
            srp.save(usr)

            for comment_oid in post.comments_oids:
                comment = srp.load(comment_oid)
                user = srp.load(comment.user_oid)
                user.delete_comment_oid(comment_oid)
                srp.save(user)

            srp.multi_delete(post.comments_oids)
            srp.delete(post_oid_fs)

            flask.flash("Publicación eliminada correctamente")
            return flask.redirect("/user/profile")

        else:
            flask.flash("Debe marcar la casilla para confirmar.")
            return flask.redirect(flask.request.url)

    else:

        return flask.render_template("delete_post.html", post_oid=post_oid)


# Permite ver un detalle con la publicación, una lista de comentarios y un formulario para añadir un nuevo comentario
# En caso de que el usuario logeado sea autor de algún comentario se le muestra la opción de eliminarlo
@flask_login.login_required
@posts_blprint.route('<string:post_oid>/comments', methods=['POST', 'GET'])
def view_comments(post_oid):
    post = srp.load(srp.oid_from_safe(post_oid))

    if not post:
        return flask.flash("post no encontrado")

    if flask.request.method == 'POST':

        message = flask.request.form.get("edMessage")

        if not message:
            flask.flash("Debes introducir un mensaje")
            return flask.redirect(flask.request.url)
        else:
            usr = UserDto.current_user()
            comment = CommentDto(message, usr.__oid__, post.__oid__)
            oid_comment = srp.save(comment)

            post.add_comment_oid(oid_comment)
            usr.add_comment_oid(oid_comment)
            srp.save(post)
            srp.save(usr)

            flask.flash("Comentario publicado correctamente")
            return flask.redirect(flask.request.url)

    else:
        usr = UserDto.current_user()
        comments_list = list(srp.load_all(CommentDto))

        sust = {

            "current_user": usr,
            "current_user_oid": srp.safe_from_oid(UserDto.current_user().__oid__),
            "user": srp.load(post.author_oid),
            "user_oid": srp.safe_from_oid(post.author_oid),
            "post": post,
            "post_oid": post_oid,
            "comments_list": comments_list,
            "comments_oids": {comment.__oid__: srp.safe_from_oid(comment.__oid__) for comment in comments_list},
            "users": {comment.__oid__: srp.load(comment.author_oid) for comment in comments_list}
        }

        return flask.render_template("view_comments.html", **sust)


# Permite, a su autor, eliminar un comentario
@flask_login.login_required
@posts_blprint.route('<string:post_oid>/comment/<string:comment_oid>/delete', methods=['POST', 'GET'])
def delete_comment(post_oid, comment_oid):
    if flask.request.method == 'POST':

        if flask.request.form.get("flexCheckDefault"):

            post = srp.load(srp.oid_from_safe(post_oid))
            oid_comment_fs = srp.oid_from_safe(comment_oid)

            post.delete_comment_oid(oid_comment_fs)
            srp.save(post)

            usr = UserDto.current_user()
            usr.delete_comment_oid(oid_comment_fs)
            srp.save(usr)

            srp.delete(oid_comment_fs)
            flask.flash("Comentario eliminado correctamente")
            return flask.redirect(url_for("posts.view_comments", post_oid=post_oid))

        else:
            flask.flash("Debes marcar la casilla para confirmar.")
            return flask.redirect(flask.request.url)

    else:
        sust = {
            "post_oid": post_oid,
            "comment_oid": comment_oid
        }
        return flask.render_template("delete_comment.html", **sust)
