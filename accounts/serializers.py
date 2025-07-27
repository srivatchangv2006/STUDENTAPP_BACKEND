from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile, UserFollow

User = get_user_model()

class UserFollowSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='following.username', read_only=True)
    email = serializers.EmailField(source='following.email', read_only=True)
    profile_picture = serializers.ImageField(source='following.profile_picture', read_only=True)

    class Meta:
        model = UserFollow
        fields = ['username', 'email', 'profile_picture', 'created_at']
        read_only_fields = ['created_at']

class UserSerializer(serializers.ModelSerializer):
    profile_data = serializers.SerializerMethodField()
    follow_data = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'profile_picture', 'bio', 'created_at', 'profile_data', 'follow_data']
        read_only_fields = ('id', 'created_at')

    def get_profile_data(self, obj):
        try:
            profile = obj.profile
            return {
                'total_points': profile.total_points,
                'badge': profile.badge,
                'badge_progress': self.get_badge_progress(profile),
                'highest_streak': profile.highest_streak,
                'current_streak': profile.current_streak,
                'last_quiz_date': profile.last_quiz_date
            }
        except Profile.DoesNotExist:
            return None

    def get_badge_progress(self, profile):
        next_badge_thresholds = {
            'none': 500,    # Points needed for bronze
            'bronze': 1500, # Points needed for silver
            'gold': None,   # No next badge
            'silver': 2500  # Points needed for gold
        }
        
        next_threshold = next_badge_thresholds.get(profile.badge)
        if next_threshold is None:
            return {
                'current': profile.badge,
                'next': None,
                'points_needed': 0,
                'progress_percentage': 100
            }
        
        current_points = profile.total_points
        previous_threshold = {
            'none': 0,
            'bronze': 500,
            'silver': 1500
        }.get(profile.badge, 0)
        
        points_needed = next_threshold - current_points
        progress = ((current_points - previous_threshold) / 
                   (next_threshold - previous_threshold)) * 100
        
        return {
            'current': profile.badge,
            'next': self.get_next_badge(profile.badge),
            'points_needed': points_needed,
            'progress_percentage': min(100, max(0, progress))
        }

    def get_next_badge(self, current_badge):
        badge_progression = {
            'none': 'bronze',
            'bronze': 'silver',
            'silver': 'gold',
            'gold': None
        }
        return badge_progression.get(current_badge)

    def get_follow_data(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return {
                'followers_count': obj.followers.count(),
                'following_count': obj.following.count(),
                'is_following': obj.followers.filter(follower=request.user).exists() if request.user != obj else None
            }
        return None

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'username', 'password', 'password2', 'profile_picture', 'bio')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    badge_progress = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = ['username', 'email', 'total_points', 'badge', 'badge_progress', 
                 'highest_streak', 'current_streak', 'last_quiz_date']
        read_only_fields = ['total_points', 'badge', 'highest_streak', 'current_streak', 'last_quiz_date']

    def get_badge_progress(self, obj):
        next_badge_thresholds = {
            'none': 500,    # Points needed for bronze
            'bronze': 1500, # Points needed for silver
            'gold': None,   # No next badge
            'silver': 2500  # Points needed for gold
        }
        
        next_threshold = next_badge_thresholds.get(obj.badge)
        if next_threshold is None:
            return {
                'current': obj.badge,
                'next': None,
                'points_needed': 0,
                'progress_percentage': 100
            }
        
        current_points = obj.total_points
        previous_threshold = {
            'none': 0,
            'bronze': 500,
            'silver': 1500
        }.get(obj.badge, 0)
        
        points_needed = next_threshold - current_points
        progress = ((current_points - previous_threshold) / 
                   (next_threshold - previous_threshold)) * 100
        
        return {
            'current': obj.badge,
            'next': self.get_next_badge(obj.badge),
            'points_needed': points_needed,
            'progress_percentage': min(100, max(0, progress))
        }

    def get_next_badge(self, current_badge):
        badge_progression = {
            'none': 'bronze',
            'bronze': 'silver',
            'silver': 'gold',
            'gold': None
        }
        return badge_progression.get(current_badge) 