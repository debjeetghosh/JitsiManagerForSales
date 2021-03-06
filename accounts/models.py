import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.
class MyUserManager(BaseUserManager):
    def create_superuser(self, email, username, password=None):
        user = self.model(
            email=self.normalize_email(email),
            username=username
        )
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        profile = UserProfile.objects.create(
            user=user,
            user_uid=uuid.uuid4(),
            user_type=UserProfile.ADMIN,
            name=username
        )
        return user



class JitsiUser(AbstractUser):
    objects = MyUserManager()


class UserProfile(models.Model):
    SALES_PERSON, ADMIN = 'sales_person', 'admin'
    USER_TYPE_CHOICES = ((SALES_PERSON, "Sales Person"), (ADMIN, "Admin member"), )

    user = models.OneToOneField(JitsiUser, models.CASCADE, related_name='profile')
    user_uid = models.CharField(max_length=255, default='')
    name = models.CharField(max_length=255)
    user_type = models.CharField(choices=USER_TYPE_CHOICES, max_length=255)
    totp_key = models.CharField(max_length=20, null=True)
    user_city = models.ForeignKey('Location', models.CASCADE, related_name='city_users', null=True)
    user_state = models.ForeignKey('Location', models.CASCADE, related_name='state_users', null=True)


class Location(models.Model):
    COUNTRY, STATE, CITY = 'country', 'state', 'city'
    location_type_choices = (
        (COUNTRY, 'country'),
        (STATE, 'state'),
        (CITY, 'city'),
    )

    name = models.CharField(max_length=255)
    parent_location = models.ForeignKey('Location', models.CASCADE, related_name='child', null=True)
    location_type = models.CharField(max_length=255, choices=location_type_choices)

    def __str__(self):
        return self.name+" ("+self.location_type+")"

    def get_all_childs(self):
        return Location.objects.filter(parent_location = self)

    def get_childs_by_type(self, loc_type):
        return self.get_all_childs().filter(location_type=loc_type)


class VerificationCode(models.Model):
    user = models.ForeignKey(JitsiUser, on_delete=models.CASCADE)
    email = models.EmailField()
    code = models.CharField(max_length=50)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True)


    def __str__(self):
        return self.email
