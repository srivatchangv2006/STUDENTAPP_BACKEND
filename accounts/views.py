from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, UserRegistrationSerializer
from rest_framework.decorators import action
from rest_framework import viewsets
from .models import UserFollow
from .serializers import UserFollowSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserRegistrationSerializer

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

class UserViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['POST'])
    def follow(self, request, pk=None):
        user_to_follow = self.get_object()
        if user_to_follow == request.user:
            return Response(
                {'error': 'You cannot follow yourself'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        follow, created = UserFollow.objects.get_or_create(
            follower=request.user,
            following=user_to_follow
        )
        
        if created:
            return Response({'status': 'following'}, status=status.HTTP_201_CREATED)
        return Response(
            {'error': 'Already following'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True, methods=['POST'])
    def unfollow(self, request, pk=None):
        user_to_unfollow = self.get_object()
        try:
            follow = UserFollow.objects.get(
                follower=request.user,
                following=user_to_unfollow
            )
            follow.delete()
            return Response({'status': 'unfollowed'}, status=status.HTTP_200_OK)
        except UserFollow.DoesNotExist:
            return Response(
                {'error': 'Not following this user'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['GET'])
    def followers(self, request, pk=None):
        user = self.get_object()
        followers = UserFollow.objects.filter(following=user)
        serializer = UserFollowSerializer(
            followers, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['GET'])
    def following(self, request, pk=None):
        user = self.get_object()
        following = UserFollow.objects.filter(follower=user)
        serializer = UserFollowSerializer(
            following, 
            many=True, 
            context={'request': request}
        )
        return Response(serializer.data)
