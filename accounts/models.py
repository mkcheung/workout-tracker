from django.conf import settings
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile"
    )

    age = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_lbs = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    height_in = models.PositiveSmallIntegerField(null=True, blank=True)
    max_heart_rate = models.PositiveSmallIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"