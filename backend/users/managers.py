from django.contrib.auth.models import UserManager


class SuperUserManager(UserManager):
    def create_superuser(
            self, username,
            email=None,
            password=None,
            **extra_fields
    ):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        user = self.model(username=username, email=email, **extra_fields)
        user.first_name = input("Введите имя пользователя: ")
        user.last_name = input("Введите фамилию пользователя: ")
        user.set_password(password)
        user.save(using=self._db)
        return user
