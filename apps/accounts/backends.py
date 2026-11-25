"""Аутентификация по логину или e-mail."""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Позволяет входить и по username, и по e-mail (без учёта регистра)."""

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None

        user = (
            UserModel.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))
            .order_by("pk")
            .first()
        )

        if user is None:
            # Выравниваем время ответа, чтобы нельзя было перебирать e-mail.
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
