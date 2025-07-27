from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from accounts.models import Profile

class Story(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    pdf_file = models.FileField(upload_to='pdf_files/')
    generated_story = models.TextField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Quiz(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=500, default='Option A')
    option_b = models.CharField(max_length=500, default='Option B')
    option_c = models.CharField(max_length=500, default='Option C')
    option_d = models.CharField(max_length=500, default='Option D')
    correct_answer = models.CharField(max_length=1, default='A')  # A, B, C, or D
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.question_text

class QuizAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    emotions_log = models.JSONField(default=dict)
    emotion_data_file = models.FileField(upload_to='emotion_data/', null=True, blank=True)
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['user', 'quiz']

    def __str__(self):
        return f"{self.user.username}'s attempt on {self.quiz.title}"

    def calculate_score(self):
        total_questions = self.quiz.questions.count()
        if total_questions == 0:
            return 0
        correct_answers = self.answers.filter(is_correct=True).count()
        return (correct_answers / total_questions) * 100

    def calculate_points(self):
        difficulty_points = {
            'easy': 10,
            'medium': 20,
            'hard': 30
        }
        max_points = difficulty_points.get(self.quiz.story.difficulty, 10)
        score_percentage = self.score / 100 if self.score else 0
        return int(max_points * score_percentage)

    def award_points(self):
        if not self.completed or hasattr(self, '_points_awarded'):
            return
        
        points_earned = self.calculate_points()
        profile = self.user.profile
        profile.add_points(points_earned)
        profile.update_streak()
        self._points_awarded = True

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if not is_new and self.completed:
            self.award_points()

class Answer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    user_answer = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    answered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Answer to {self.question} by {self.attempt.user.username}"
