from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Profile

User = get_user_model()

class RegisterSerializer(serializer.ModelSerializer):
    model = User
    fields = ['username', 'email', 'password']

    def validate_password(self, value):
        validate_password(value)
        return value
        
    def create(self, validated_data):
        user = User.objects.create_user(
            user_name = validated_data('username'),
            email = validated_data('email'),
            password = validated_data('password')
        )
        return user
        
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['age', 'weight_lbs', 'height_in', 'max_heart_rate']

class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile']
        read_only_fields = ['id', 'username']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile')
        instance = super().update(instance, validated_data)

        user_profile = instance.profile
        for key, value in profile_data.items():
            setattr(user_profile, key, value)
        user_profile.save()

        return instance