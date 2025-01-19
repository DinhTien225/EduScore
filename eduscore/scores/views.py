from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from . import serializers, paginators
from .models import Category, Activity, Participation, DisciplinePoint, Report, User, Comment, NewsFeed,Like
from scores import perms

class CategoryViewSet(viewsets.ViewSet, generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = serializers.CategorySerializer
    pagination_class = paginators.ItemPaginator


class ActivityViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Activity.objects.prefetch_related('tags').filter(active=True)
    serializer_class = serializers.ActivityDetailsSerializer
    pagination_class = paginators.ItemPaginator

    def get_queryset(self):
        query = self.queryset

        category_id = self.request.query_params.get('category_id')
        if category_id:
            query = query.filter(category_id=category_id)

        search_keyword = self.request.query_params.get('q')
        if search_keyword:
            query = query.filter(title__icontains=search_keyword)

        tag_name = self.request.query_params.get('tag')
        if tag_name:
            query = query.filter(tags__name=tag_name)

        return query

    @action(methods=['get'], url_path='participations', detail=True)
    def get_participations(self, request, pk):
        activity = self.get_object().participation_set.filter(active=True)

        return Response(serializers.ParticipationSerializer(activity, many=True, context={'request': request}).data)


class ParticipationViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = Participation.objects.filter(active=True)
    serializer_class = serializers.ParticipationSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        if self.action == 'student_participation_history':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    @action(methods=['post'], url_path='complete', detail=True)
    def mark_complete(self, request, pk):
        participation = self.get_object()
        participation.is_completed = True
        participation.save()

        return Response(serializers.ParticipationSerializer(participation).data)

    @action(methods=['get'], url_path='student-history', detail=False)
    def student_participation_history(self, request):
        participations = Participation.objects.filter(student=request.user, active=True)
        return Response(serializers.ParticipationSerializer(participations, many=True).data)


class DisciplinePointViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = DisciplinePoint.objects.all()
    serializer_class = serializers.DisciplinePointSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.IsAuthenticated()]
        return super().get_permissions()

    def get_queryset(self):
        query = self.queryset
        if self.request.user.is_superuser:
            return query

        if self.request.user.is_staff:
            student_id = self.request.query_params.get('student_id')
            if student_id:
                query = query.filter(student_id=student_id)

        if not self.request.user.is_staff and not self.request.user.is_superuser:
            query = query.filter(student=self.request.user)

        return query


class ReportViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = Report.objects.filter(active=True)
    serializer_class = serializers.ReportSerializer
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

    def get_permissions(self):
        if self.request.method == 'GET':
            if self.request.user.is_superuser:
                return [permissions.IsAuthenticated()]
            elif self.request.user.is_staff:
                return [permissions.IsAuthenticated()]
            return [permissions.IsAuthenticated()]

    @action(methods=['patch'], url_path='approve', detail=True)
    def approve_report(self, request, pk):
        report = self.get_object()
        report.status = 'approved'
        report.handled_by = request.user
        report.save()
        return Response(serializers.ReportSerializer(report).data)

    @action(methods=['patch'], url_path='reject', detail=True)
    def reject_report(self, request, pk):
        report = self.get_object()
        report.status = 'rejected'
        report.handled_by = request.user
        report.save()
        return Response(serializers.ReportSerializer(report).data)


class UserViewSet(viewsets.ViewSet, generics.CreateAPIView):
    queryset = User.objects.filter(is_active=True)
    serializer_class = serializers.UserSerializer

    @action(methods=['get'], url_path='current-user', detail=False, permission_classes=[permissions.IsAuthenticated])
    def get_current_user(self, request):
        return Response(serializers.UserSerializer(request.user).data)


    @action(methods=['post'], url_path='change-password', detail=False,
            permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        serializer = serializers.ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Password changed successfully'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class NewsFeedViewSet(viewsets.ViewSet, generics.ListCreateAPIView):
    queryset = NewsFeed.objects.filter(active=True)
    serializer_class = serializers.NewsFeedSerializer
    pagination_class = paginators.ItemPaginator
    permission_classes = [permissions.IsAdminUser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        if self.action in ['get_comments','get_likes']:
            if self.request.method.__eq__('POST'):
                return [permissions.IsAuthenticated()]
            return [permissions.AllowAny()]

        return super().get_permissions()

    @action(methods=['get', 'post'], url_path='comments', detail=True)
    def get_comments(self, request, pk):
        if request.method.__eq__('POST'):
            content = request.data.get('content')
            c = Comment.objects.create(content=content, user=request.user, newsfeed=self.get_object())

            return Response(serializers.CommentSerializer(c).data)
        else:
            comments = self.get_object().comment_set.select_related('user').filter(active=True)
            return Response(serializers.CommentSerializer(comments, many=True).data)

    @action(methods=['get', 'post'], url_path='likes', detail=True)
    def get_likes(self, request, pk):
        newsfeed = self.get_object()

        if request.method.__eq__('GET'):
            likes = newsfeed.like_set.select_related('user')
            serializer = serializers.UserSerializer([like.user for like in likes], many=True)
            return Response(serializer.data)

        if request.method.__eq__('POST'):
            like, created = Like.objects.get_or_create(user=request.user, newsfeed=newsfeed)
            if not created:
                like.delete()
                return Response({'message': 'Unliked successfully.'}, status=status.HTTP_200_OK)

            return Response({'message': 'Liked successfully.'}, status=status.HTTP_201_CREATED)

class CommentViewSet(viewsets.ViewSet, generics.DestroyAPIView):
    queryset = Comment.objects.filter(active=True)
    serializer_class = serializers.CommentSerializer
    permission_classes = [perms.OwnerPerms]
