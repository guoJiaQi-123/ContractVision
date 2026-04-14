from django.contrib.auth import authenticate
from rest_framework import serializers

from utils.validators import validate_password_strength

from .models import User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'company_name',
            'department', 'region', 'role', 'is_active',
            'avatar', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'phone', 'company_name', 'department', 'region',
        ]

    def validate_password(self, value):
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs.pop('confirm_password'):
            raise serializers.ValidationError({'confirm_password': '两次输入的密码不一致'})
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            phone=validated_data.get('phone', ''),
            company_name=validated_data.get('company_name', ''),
            department=validated_data.get('department', ''),
            region=validated_data.get('region', ''),
        )
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        user = authenticate(
            username=attrs['username'],
            password=attrs['password'],
        )
        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        if not user.is_active:
            raise serializers.ValidationError('该账号已被禁用')
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次输入的密码不一致'})
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    phone = serializers.CharField()
    new_password = serializers.CharField(min_length=8)
    confirm_password = serializers.CharField()

    def validate_new_password(self, value):
        validate_password_strength(value)
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': '两次输入的密码不一致'})
        try:
            user = User.objects.get(username=attrs['username'], phone=attrs['phone'])
        except User.DoesNotExist:
            raise serializers.ValidationError('用户名与手机号不匹配')
        attrs['user'] = user
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'company_name',
            'department', 'region', 'role',
            'avatar', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'username', 'role', 'created_at', 'updated_at']
