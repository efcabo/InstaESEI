from operator import attrgetter

import flask
import flask_login
import sirope
from flask import send_file, url_for

from model.UserDto import UserDto


def get_blprint():
    users = flask.blueprints.Blueprint("users", __name__,
                                       template_folder="templates",
                                       url_prefix="/user",
                                       static_folder="static")
    syrp = sirope.Sirope()

    return users, syrp


users_blprint, srp = get_blprint()


# Ver perfil del usuario logeado
# Redirige a la función general de ver vista de usuario, para poder reutilizar el código para ambos
@flask_login.login_required
@users_blprint.route("profile", methods=["GET"])
def view_current_user_profile():
    current_user_oid = srp.safe_from_oid(UserDto.current_user().__oid__)
    return flask.redirect(url_for("users.view_profile", user_oid=current_user_oid))


# Ver perfil de usuario
@flask_login.login_required
@users_blprint.route("<string:user_oid>/profile", methods=["GET"])
def view_profile(user_oid):
    user = srp.load(srp.oid_from_safe(user_oid))
    posts_list = list(srp.multi_load(user.posts_oids))
    posts_list.sort(key=attrgetter('time'), reverse=True)

    current_user = UserDto.current_user()

    sust = {
        "current_user": current_user,
        "user": user,
        "user_oid": user_oid,
        "posts_list": posts_list,
        "posts_oids": {post.__oid__: srp.safe_from_oid(post.__oid__) for post in posts_list}
    }

    return flask.render_template("view_profile.html", **sust)


# Modificar la contraseña
@flask_login.login_required
@users_blprint.route("/modify-password", methods=["POST", "GET"])
def modify_password():
    current_usr = UserDto.current_user()

    if flask.request.method == 'POST':

        old_paswd = flask.request.form.get("edContrasenaAnt")
        new_pswd_1 = flask.request.form.get("edContrasena1")
        new_pswd_2 = flask.request.form.get("edContrasena2")

        if not (old_paswd or new_pswd_1 or new_pswd_2):
            flask.flash("Debes completar todos los campos.")
            return flask.redirect(flask.request.url)
        else:
            if not (new_pswd_1 == new_pswd_2):
                flask.flash("Las contraseñas no coinciden.")
                return flask.redirect(flask.request.url)
            else:
                if not current_usr.chk_password(old_paswd):
                    flask.flash("Contraseña actual incorrecta.")
                    return flask.redirect(flask.request.url)
                else:
                    if old_paswd == new_pswd_1:
                        flask.flash("La nueva contraseña no puede coincidir con la actual.")
                        return flask.redirect(flask.request.url)
                    else:
                        current_usr.mod_password(new_pswd_1)
                        srp.save(current_usr)
                        flask.flash("Contraseña modificada correctamente")
                        return flask.redirect("profile")
    else:
        return flask.render_template("modify_password.html")


# Modificar imagen de perfil
# Por defecto la imagen de perfil es un icono generico, pero se puede establecer una personalizada
@flask_login.login_required
@users_blprint.route("/modify-profile-image", methods=["POST", "GET"])
def modify_profile_image():
    if flask.request.method == 'POST':
        image = flask.request.files['file']

        if image.filename == '':
            flask.flash("Selecciona una imagen.")
            return flask.redirect(flask.request.url)

        else:
            user = UserDto.current_user()
            user.profile_image = image
            srp.save(user)
            flask.flash("Foto de perfil modificada.")
            return flask.redirect("/user/profile")

    return flask.render_template("modify_profile_image.html")


# Genera una ruta para mostrar las imagenes de los posts
@flask_login.login_required
@users_blprint.route('get_image/<string:user_oid>')
def get_image(user_oid):
    user = srp.load(srp.oid_from_safe(user_oid))
    image = user.profile_image
    return send_file(image, mimetype='/image/png')


# Permite al usuario eliminar su cuenta
# Al eliminar el usuario tambien:
# Se eliminan publicaciones creadas por el usuario y sus comentarios asociados
# Se eliminan comentarios realizados por el usuario
# Se reduce en 1 el numero de seguidores de los usuarios a los que sigue
@flask_login.login_required
@users_blprint.route("/delete", methods=["POST", "GET"])
def delete_user():
    if flask.request.method == 'POST':

        if flask.request.form.get("flexCheckDefault"):
            current_user = UserDto.current_user()

            for post_oid in current_user.posts_oids:
                post = srp.load(post_oid)
                for comment_oid in post.comments_oids:
                    comment = srp.load(comment_oid)
                    user = srp.load(comment.user_oid)
                    user.delete_comment_oid(comment_oid)
                    srp.save(user)

                srp.multi_delete(post.comments_oids)

            for comment_oid in current_user.comments_oids:
                comment = srp.load(comment_oid)
                post = srp.load(comment.post_oid)
                post.delete_comment_oid(comment_oid)
                srp.save(post)

            for foll_user_oid in current_user.following_oids:
                foll_user = srp.load(foll_user_oid)
                foll_user.delete_follower()
                srp.save(foll_user)

            srp.multi_delete(current_user.comments_oids)
            srp.multi_delete(current_user.posts_oids)
            srp.delete(current_user.__oid__)

            flask.flash("Usuario eliminado correctamente.")
            return flask.redirect("/logout")

        else:
            flask.flash("Marcar la casilla para confirmar.")
            return flask.redirect(flask.request.url)
    else:

        return flask.render_template("delete_user.html")


# Permite buscar usuarios sin tener en cuenta si el usuario los sigue o no
@flask_login.login_required
@users_blprint.route("/search", methods=["POST", "GET"])
def search_user():
    if flask.request.method == 'POST':
        search_user = flask.request.form.get("search")
        users_list = UserDto.search_by_username(srp, search_user)
        users_list = [user for user in users_list if user.username != UserDto.current_user().username]

        sust = {
            "users_list": users_list,
            "users_oids": {user.__oid__: srp.safe_from_oid(user.__oid__) for user in users_list}
        }

        return flask.render_template("search_user.html", **sust)


# Permite comenzar a seguir a un usuario
@flask_login.login_required
@users_blprint.route("/<string:user_oid>/follow", methods=["POST", "GET"])
def follow_user(user_oid):
    current_user = UserDto.current_user()

    user_oid_fs = srp.oid_from_safe(user_oid)

    if srp.oid_from_safe(user_oid) not in current_user.following_oids:
        current_user.add_following_oid(user_oid_fs)
        srp.save(current_user)

        current_user = srp.load(user_oid_fs)
        current_user.add_follower()
        srp.save(current_user)

    return flask.redirect(url_for("users.view_profile", user_oid=user_oid))


# Permite dejar de seguir a un usuario
@flask_login.login_required
@users_blprint.route("/<string:user_oid>/unfollow", methods=["POST", "GET"])
def unfollow_user(user_oid):
    current_user = UserDto.current_user()
    user_oid_fs = srp.oid_from_safe(user_oid)

    if user_oid_fs in current_user.following_oids:
        current_user.delete_following_oid(user_oid_fs)
        srp.save(current_user)

        user = srp.load(user_oid_fs)
        user.delete_follower()
        srp.save(user)

    return flask.redirect(url_for("users.view_profile", user_oid=user_oid))
