import flask
import flask_login
import sirope

from model.UserDto import UserDto


def get_blprint():
    login = flask.blueprints.Blueprint("login", __name__,
                                       template_folder="templates",
                                       static_folder="static")
    syrp = sirope.Sirope()

    return login, syrp


login_blprint, srp = get_blprint()


# Iniciar sesion
@login_blprint.route("/signin", methods=["POST", "GET"])
def signin():
    if flask.request.method == 'POST':

        # El usuario puede identificarse tanto con su usuario como mediante el correo electronico
        id_user = flask.request.form.get("edId")
        password = flask.request.form.get("edContrasena")

        if not id_user:
            flask.flash("Introduce el usuario o correo electrónico.")
            return flask.redirect(flask.request.url)
        else:
            if not password:
                flask.flash("Introduce la contraseña.")
                return flask.redirect(flask.request.url)

            # En caso de que la cadena introducida no coincida con un email valido se comprueba el usuario
            user = UserDto.find_by_email(srp, id_user)
            if not user:
                user = UserDto.find_by_username(srp, id_user)

            if not user:
                flask.flash("Usuario o correo electrónico incorrecto.")
                return flask.redirect(flask.request.url)
            elif not user.chk_password(password):
                flask.flash("Contraseña incorrecta.")
                return flask.redirect(flask.request.url)

            flask_login.login_user(user)
            return flask.redirect("/")

    else:
        return flask.render_template("signin.html")


# Registrarse
@login_blprint.route("/signup", methods=["POST", "GET"])
def signup():
    if flask.request.method == 'POST':
        email = flask.request.form.get("edEmail")
        usuario = flask.request.form.get("edUsuario")
        password_1 = flask.request.form.get("edContrasena1")
        password_2 = flask.request.form.get("edContrasena2")

        if not email:
            flask.flash("Introduce el email.")
            return flask.redirect(flask.request.url)
        else:
            if not usuario:
                flask.flash("Introduce el usuario.")
                return flask.redirect(flask.request.url)
            else:
                if not (password_1 or password_2):
                    flask.flash("Introduce la contraseña.")
                    return flask.redirect(flask.request.url)
                elif password_1 != password_2:
                    flask.flash("Las contraseñas no coinciden.")
                    return flask.redirect(flask.request.url)
                else:

                    # Para poder iniciar sesion tanto con el usuario como con el email ambos deben ser unicos
                    usr_email = UserDto.find_by_email(srp, email)
                    usr_username = UserDto.find_by_email(srp, usuario)

                    if usr_email:
                        if usr_username:
                            flask.flash("Usuario en uso.")
                            return flask.redirect(flask.request.url)

                        flask.flash("Correo electrónico en uso.")
                        return flask.redirect(flask.request.url)

                    user = UserDto(usuario, email, password_1)
                    srp.save(user)

                    flask.flash("Usuario registrado correctamente.")
                    return flask.redirect("/signin")
    else:
        return flask.render_template("signup.html")


# Cerrar sesion
@login_blprint.route('/logout')
def logout():
    flask_login.logout_user()
    flask.flash("Sesión finalizada correctamente.")
    return flask.redirect("/")
