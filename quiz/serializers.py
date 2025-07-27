from rest_framework import serializers
from .models import Story, Quiz, Question, QuizAttempt, Answer

class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ('id', 'quiz', 'question_text', 'options', 'correct_answer', 'created_at')
        read_only_fields = ('created_at',)
        extra_kwargs = {'correct_answer': {'write_only': True}}

    def get_options(self, obj):
        # Return options A-D for each question
        return [
            f"A) {obj.option_a}",
            f"B) {obj.option_b}",
            f"C) {obj.option_c}",
            f"D) {obj.option_d}"
        ]

class QuizSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    questions_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ('id', 'story', 'title', 'created_at', 'questions', 'questions_count')
        read_only_fields = ('created_at',)

    def get_questions_count(self, obj):
        return obj.questions.count()

class StorySerializer(serializers.ModelSerializer):
    quizzes = QuizSerializer(many=True, read_only=True)

    class Meta:
        model = Story
        fields = ('id', 'user', 'title', 'pdf_file', 'generated_story', 'difficulty', 'created_at', 'quizzes')
        read_only_fields = ('user', 'generated_story', 'created_at')

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ('id', 'attempt', 'question', 'user_answer', 'is_correct', 'answered_at')
        read_only_fields = ('is_correct', 'answered_at')

class QuizAttemptSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    quiz_details = QuizSerializer(source='quiz', read_only=True)
    emotion_data_file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = QuizAttempt
        fields = ('id', 'user', 'quiz', 'quiz_details', 'score', 'emotions_log', 
                 'emotion_data_file', 'completed', 'started_at', 'completed_at', 'answers')
        read_only_fields = ('user', 'score', 'completed', 'started_at', 'completed_at') 