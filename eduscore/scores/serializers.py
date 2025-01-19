from rest_framework import serializers
from .models import *
from django.contrib.auth.password_validation import validate_password

class BaseSerializer (serializers.ModelSerializer):
    image = serializers.SerializerMethodField(source='image')

    def get_image(self, activity):
        if activity.image:
            if activity.image.name.startswith("http"):
                return activity.image.name

            request = self.context.get('request')
            if request:
                return request.build_absolute_uri('/static/%s' % activity.image.name)

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name']

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class UserSerializer(serializers.ModelSerializer):
    def create(self, validated_data):
        data = validated_data.copy()
        u = User(**data)
        u.set_password(u.password)
        u.save()
        return u

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['avatar'] = instance.avatar.url if instance.avatar else ''
        return data

    class Meta:
        model = User
        fields = ['id', 'username','password', 'first_name', 'last_name','avatar']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

class ActivitySerializer(BaseSerializer):
    class Meta:
        model = Activity
        fields = ['id', 'title', 'description', 'start_date', 'end_date', 'created_by', 'capacity', 'status', 'category','image','tags']

class ActivityDetailsSerializer(ActivitySerializer):
    tags = TagSerializer(many=True)

    class Meta:
        model = ActivitySerializer.Meta.model
        fields = ActivitySerializer.Meta.fields + ['title', 'tags']

class ParticipationSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    activity = serializers.PrimaryKeyRelatedField(queryset=Activity.objects.all())

    class Meta:
        model = Participation
        fields = ['id', 'student', 'activity', 'is_completed', 'proof']


class DisciplinePointSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisciplinePoint
        fields = ['id', 'student','activity', 'criteria', 'score', 'total_score']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'activity', 'proof', 'status', 'handled_by']
        read_only_fields = ['student']

class NewsFeedSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewsFeed
        fields = ['id', 'activity', 'created_date']
        read_only_fields = ['created_by']

class LikeSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    newsfeed = NewsFeedSerializer()

    class Meta:
        model = Like
        fields = ['id', 'user', 'newsfeed']


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'newsfeed', 'content', 'created_date']


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer()
    receiver = UserSerializer()

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp']

class StudentRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all(), required=False)
    student_class = serializers.PrimaryKeyRelatedField(queryset=Class.objects.all(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'confirm_password', 'avatar', 'department', 'student_class']

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        if not value.endswith('@school.edu'):  # Adjust domain validation as needed
            raise serializers.ValidationError("Email must be a valid school email.")
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        department = validated_data.pop('department', None)
        student_class = validated_data.pop('student_class', None)

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        user.avatar = validated_data.get('avatar', None)
        user.department = department
        user.student_class = student_class
        user.save()
        return user

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, required=True)
    new_password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords didn't match."})
        if attrs['new_password'] == attrs['old_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the old password."})
        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
