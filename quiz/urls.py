from django.urls import path
from .views import (
    StoryCreateView, QuizAttemptCreateView, SubmitAnswerView,
    QuizAttemptDetailView, UserQuizHistoryView, StartQuizAttemptView,
    RegenerateQuizView, UserPointsView, LeaderboardView
)

urlpatterns = [
    path('stories/create/', StoryCreateView.as_view(), name='create-story'),
    path('attempts/create/', QuizAttemptCreateView.as_view(), name='create-attempt'),
    path('attempts/<int:attempt_id>/submit/', SubmitAnswerView.as_view(), name='submit-answer'),
    path('attempts/<int:pk>/', QuizAttemptDetailView.as_view(), name='attempt-detail'),
    path('history/', UserQuizHistoryView.as_view(), name='quiz-history'),
    path('stories/<int:story_id>/regenerate/', RegenerateQuizView.as_view(), name='regenerate-quiz'),
    path('points/', UserPointsView.as_view(), name='user-points'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
] 