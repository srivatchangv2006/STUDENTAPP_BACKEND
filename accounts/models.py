from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_points = models.IntegerField(default=0)
    badge = models.CharField(
        max_length=10,
        choices=[
            ('none', 'No Badge'),
            ('bronze', 'Bronze'),
            ('silver', 'Silver'),
            ('gold', 'Gold')
        ],
        default='none'
    )
    highest_streak = models.IntegerField(default=0)
    current_streak = models.IntegerField(default=0)
    last_quiz_date = models.DateField(null=True, blank=True)

    def update_badge(self):
        if self.total_points >= 2500:
            self.badge = 'gold'
        elif self.total_points >= 1500:
            self.badge = 'silver'
        elif self.total_points >= 500:
            self.badge = 'bronze'
        else:
            self.badge = 'none'
        self.save()

    def add_points(self, points):
        self.total_points += points
        self.update_badge()

    def update_streak(self):
        today = timezone.now().date()
        if self.last_quiz_date:
            days_diff = (today - self.last_quiz_date).days
            if days_diff == 1:  # consecutive day
                self.current_streak += 1
                self.highest_streak = max(self.current_streak, self.highest_streak)
            elif days_diff > 1:  # streak broken
                self.current_streak = 1
        else:
            self.current_streak = 1
        
        self.last_quiz_date = today
        self.save()

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

class UserFollow(models.Model):
    follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')
        
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
