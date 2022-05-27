import flask
import flask_login
import sirope
from operator import attrgetter
from flask_login import login_manager
from model.PostDto import PostDto
from model.UserDto import UserDto
from views.login import login_view
from views.posts import posts_view
from views.users import users_view


def create_app():
    lmanager = login_manager.LoginManager()
    fapp = flask.Flask(__name__, instance_relative_config=True)
    syrp = sirope.Sirope()

    fapp.config['SECRET_KEY'] = "192b9bdd22ab9ed4d12e236c78afcb9a393ec15f71bbf5dc987d54727823bcbf"
    lmanager.init_app(fapp)
    fapp.register_blueprint(login_view.login_blprint)
    fapp.register_blueprint(users_view.users_blprint)
    fapp.register_blueprint(posts_view.posts_blprint)
    return fapp, lmanager, syrp


app, lm, srp = create_app()


@lm.user_loader
def user_loader(email):
    return UserDto.find_by_email(srp, email)


# Si hay una sesión iniciada, cargamos la página de inicio de la aplicación.
# En caso contrario redirigimos al usuario para que inicie sesion o se registre
@app.route('/')
def get_index():
    usr = UserDto.current_user()

    if not usr:
        return flask.redirect("/signin")
    else:
        return flask.redirect("/home")


# Carga la plantilla de la página principal, donde se muestran las publicaciones de
# aquellos usuarios a los que el usuario logeado sigue
@flask_login.login_required
@app.route('/home')
def home():
    current_user = UserDto.current_user()
    posts_list = list(srp.load_all(PostDto))
    posts_list = [post for post in posts_list
                  if post.author_oid != current_user.__oid__ and post.author_oid in current_user.following_oids]

    posts_list.sort(key=attrgetter('time'), reverse=True)

    sust = {
        "posts_list": posts_list,
        "posts_oids": {post.__oid__: srp.safe_from_oid(post.__oid__) for post in posts_list},
        "users_list": {post.__oid__: srp.load(post.author_oid) for post in posts_list},
        "users_oids": {post.__oid__: srp.safe_from_oid(post.author_oid) for post in posts_list},
    }

    return flask.render_template("home.html", **sust)


@lm.unauthorized_handler
def unauthorized_handler():
    flask.flash("Unauthorized")
    return flask.redirect("/")


if __name__ == '__main__':
    app.run()
