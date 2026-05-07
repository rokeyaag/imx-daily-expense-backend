from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
import cloudinary

class RegisterSerializer(serializers.ModelSerializer):
    password  = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)
    class Meta:
        model  = User
        fields = ["email", "name", "password", "password2", "currency"]
    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data
    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(**validated_data)

class LoginSerializer(serializers.Serializer):
    email    = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        user = authenticate(username=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("Account is disabled.")
        data["user"] = user
        return data

class UserProfileSerializer(serializers.ModelSerializer):
    avatar     = serializers.SerializerMethodField()
    avatar_url = serializers.CharField(write_only=True, required=False)
    class Meta:
        model  = User
        fields = ["id", "email", "name", "currency", "avatar", "avatar_url", "created_at"]
        read_only_fields = ["id", "email", "created_at"]
    def get_avatar(self, obj):
        if not obj.avatar:
            return None
        av = str(obj.avatar)
        if av.startswith("http"):
            return av
        try:
            return cloudinary.CloudinaryImage(av).build_url(secure=True)
        except:
            return av
    def update(self, instance, validated_data):
        avatar_url = validated_data.pop("avatar_url", None)
        if avatar_url:
            instance.avatar = avatar_url
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
