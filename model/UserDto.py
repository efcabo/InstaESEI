import sirope
import flask_login
from io import BytesIO
from PIL import Image
from sirope import OID
import werkzeug.security as safe
from werkzeug.datastructures import FileStorage


class UserDto(flask_login.UserMixin):
    def __init__(self, username: str, email: str, password: str):
        self._username = username
        self._email = email
        self._password = safe.generate_password_hash(password)
        self._profile_image = None
        self._posts_oids = []
        self._comments_oids = []
        self._following_oids = []
        self._num_followers = 0

    @property
    def email(self) -> str:
        return self._email

    @property
    def username(self) -> str:
        return self._username

    def get_id(self) -> str:
        return self.email

    @property
    def profile_image(self) -> BytesIO | None:
        if self._profile_image is None:
            return None
        return BytesIO(self._profile_image)

    @profile_image.setter
    def profile_image(self, image: FileStorage):
        image = Image.open(image)
        image = image.resize((500, 500))

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self._profile_image = img_byte_arr

    @property
    def posts_oids(self) -> list:
        return self._posts_oids

    def add_post_oid(self, post_oid: OID):
        self._posts_oids.append(post_oid)

    def delete_post_oid(self, post_oid: OID):
        self._posts_oids.remove(post_oid)

    @property
    def comments_oids(self) -> list:
        return self._comments_oids

    def add_comment_oid(self, comment_oid: OID):
        self._comments_oids.append(comment_oid)

    def delete_comment_oid(self, comment_oid: OID):
        self._comments_oids.remove(comment_oid)

    @property
    def following_oids(self) -> list:
        return self._following_oids

    def add_following_oid(self, following_oid: OID):
        self._following_oids.append(following_oid)

    def delete_following_oid(self, following_oid: OID):
        self._following_oids.remove(following_oid)

    def num_following(self) -> int:
        return len(self._following_oids)

    def chk_password(self, password: str) -> bool:
        return safe.check_password_hash(self._password, password)

    def mod_password(self, password: str):
        self._password = safe.generate_password_hash(password)

    @property
    def num_followers(self) -> int:
        return self._num_followers

    def add_follower(self):
        self._num_followers += 1

    def delete_follower(self):
        self._num_followers -= 1

    @staticmethod
    def current_user() -> "UserDto":
        usr = flask_login.current_user

        if usr.is_anonymous:
            flask_login.logout_user()
            usr = None

        return usr

    @staticmethod
    def find_by_email(s: sirope.Sirope, email: str) -> "UserDto":
        return s.find_first(UserDto, lambda u: u.email == email)

    @staticmethod
    def find_by_username(s: sirope.Sirope, username: str) -> "UserDto":
        return s.find_first(UserDto, lambda u: u.username == username)

    @staticmethod
    def search_by_username(s: sirope.Sirope, username: str) -> list:
        return [user for user in list(s.load_all(UserDto)) if username.lower() in user.username.lower()]
