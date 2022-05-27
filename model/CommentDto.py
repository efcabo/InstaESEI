from datetime import datetime
from sirope import OID


class CommentDto:
    def __init__(self, message: str, author_oid: OID, post_oid: OID):
        self._message = message
        self._time = datetime.now()
        self._author_oid = author_oid
        self._post_oid = post_oid

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
    def post_oid(self) -> OID:
        return self._post_oid
