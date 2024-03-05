from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, first_name, last_name, phone_no, gender, dob, username, email, password=None):
        if not email:
            raise ValueError("User must have an email address")
        if not username:
            raise ValueError("User must have an username")
        user = self.model(
            email = self.normalize_email(email),
            username = username,
            first_name = first_name,
            last_name = last_name,
            phone_no = phone_no,
            gender = gender,
            dob = dob,
        )
        user.set_password(password)
        user.save(using = self._db)
        return user





class User(AbstractBaseUser):
    pass 