from io import BytesIO
from PIL import Image
from sirope import OID
from datetime import datetime
from werkzeug.datastructures import FileStorage


class PostDto:
    def __init__(self, image: FileStorage, message: str, author_oid: OID):
        self.image = image
        self._message = message
        self._time = datetime.now()
        self._author_oid = author_oid
        self._comments_oids = []

    @property
    def image(self) -> BytesIO:
        return BytesIO(self._image)

    @image.setter
    def image(self, image: FileStorage):
        image = Image.open(image)
        image = image.resize((500, 500))

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()

        self._image = img_byte_arr

    @property
    def message(self) -> str:
        return self._message

    @message.setter
    def message(self, message: str):
        self._message = message

    @property
    def time(self) -> datetime:
        return self._time.replace(microsecond=0)

    @property
    def author_oid(self) -> OID:
        return self._author_oid

    @property
    def comments_oids(self) -> list:
        return self._comments_oids

    def add_comment_oid(self, comment_oid: OID):
        self._comments_oids.append(comment_oid)

    def delete_comment_oid(self, comment_oid: OID):
        self._comments_oids.remove(comment_oid)
