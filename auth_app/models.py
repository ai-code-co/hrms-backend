

# Create your models here.
from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    email = models.EmailField(unique=True)
    # ⚠️ is_active already exists in AbstractUser
    is_verified = models.BooleanField(default=False)
    is_first_login = models.BooleanField(default=True)  

    USERNAME_FIELD = "username"   # login remains SAME
    REQUIRED_FIELDS = ["email", "first_name", "last_name"]

    def __str__(self):
        return self.username
