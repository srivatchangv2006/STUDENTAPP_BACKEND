from django.shortcuts import render
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Story, Quiz, Question, QuizAttempt, Answer
from .serializers import (
    StorySerializer, QuizSerializer, QuestionSerializer,
    QuizAttemptSerializer, AnswerSerializer
)
import google.generativeai as genai
from django.conf import settings
import PyPDF2
import io
from .video_processor import VideoProcessor
import threading
import time

# Configure Gemini AI
genai.configure(api_key=settings.GEMINI_API_KEY)

class StoryCreateView(generics.CreateAPIView):
    serializer_class = StorySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, *args, **kwargs):
        # Read PDF content
        pdf_file = request.FILES['pdf_file']
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        pdf_text = ""
        for page in pdf_reader.pages:
            pdf_text += page.extract_text()

        # Get difficulty level
        difficulty = request.data.get('difficulty', 'medium')
        
        # Generate story and questions using Gemini AI
        model = genai.GenerativeModel('models/gemini-1.5-flash-8b-exp-0924')
        
        # Enhanced prompts for better question generation
        difficulty_descriptions = {
            'easy': "Generate 5 basic multiple-choice questions that test fundamental understanding. Focus on key terms, definitions, and basic concepts.",
            'medium': "Generate 5 intermediate multiple-choice questions that require both understanding and application. Include questions that test relationships between concepts and practical applications.",
            'hard': "Generate 5 challenging multiple-choice questions that require deep analysis. Include questions that combine multiple concepts and require critical thinking."
        }
        
        prompt = f"""Based on the following text about algorithms and data structures, {difficulty_descriptions[difficulty]}

        Rules for question generation:
        1. Each question must have exactly 4 options (A, B, C, D)
        2. One and only one option should be correct
        3. All options should be plausible but clearly distinguishable
        4. Questions should be relevant to the text content
        5. For medium difficulty:
           - Include some questions about relationships between concepts
           - Ask about practical applications
           - Test understanding of processes and procedures

        Format each question exactly as follows (maintain this exact format):
        Q1. [Question text]
        A) [Option A]
        B) [Option B]
        C) [Option C]
        D) [Option D]
        Answer: [Correct option letter]

        Text to analyze:
        {pdf_text}"""
        
        try:
            response = model.generate_content(prompt)
            generated_content = response.text

            # Create serializer with the data
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Save the story with difficulty level
            story_instance = serializer.save(
                user=request.user,
                generated_story=pdf_text,
                difficulty=difficulty
            )

            # Create quiz
            quiz = Quiz.objects.create(
                story=story_instance,
                title=f"Quiz for {story_instance.title} ({difficulty.capitalize()})"
            )

            # Parse and create questions
            questions_data = []
            questions = [q.strip() for q in generated_content.split('\n\n') if q.strip().startswith('Q')]
            
            for q in questions:
                try:
                    lines = [line.strip() for line in q.split('\n') if line.strip()]
                    if len(lines) >= 6:
                        # Extract question components
                        question_text = lines[0].split('. ', 1)[1] if '. ' in lines[0] else lines[0]
                        options = {}
                        for i, opt in enumerate(lines[1:5]):
                            if ') ' in opt:
                                letter, text = opt.split(') ', 1)
                                options[letter] = text
                        
                        # Extract correct answer
                        correct_answer = lines[5].split(': ')[1].strip() if ': ' in lines[5] else ''
                        
                        # Validate all components are present
                        if (len(options) == 4 and 
                            all(key in options for key in ['A', 'B', 'C', 'D']) and 
                            correct_answer in ['A', 'B', 'C', 'D']):
                            
                            question = Question.objects.create(
                                quiz=quiz,
                                question_text=question_text,
                                option_a=options['A'],
                                option_b=options['B'],
                                option_c=options['C'],
                                option_d=options['D'],
                                correct_answer=correct_answer
                            )
                            
                            # Add question data for response
                            questions_data.append({
                                'id': question.id,
                                'text': question_text,
                                'options': [
                                    f"A) {options['A']}",
                                    f"B) {options['B']}",
                                    f"C) {options['C']}",
                                    f"D) {options['D']}"
                                ]
                            })
                except Exception as e:
                    print(f"Error parsing question: {str(e)}")
                    continue

            # If no questions were created, try again with simplified prompt
            if not questions_data:
                simplified_prompt = f"""Generate 5 multiple-choice questions about this text. Each question must have exactly 4 options (A, B, C, D) and one correct answer.

                Format:
                Q1. [Question]
                A) [Option]
                B) [Option]
                C) [Option]
                D) [Option]
                Answer: [A/B/C/D]

                Text: {pdf_text}"""
                
                retry_response = model.generate_content(simplified_prompt)
                retry_content = retry_response.text
                
                retry_questions = [q.strip() for q in retry_content.split('\n\n') if q.strip().startswith('Q')]
                for q in retry_questions:
                    try:
                        lines = [line.strip() for line in q.split('\n') if line.strip()]
                        if len(lines) >= 6:
                            question_text = lines[0].split('. ', 1)[1] if '. ' in lines[0] else lines[0]
                            options = {}
                            for i, opt in enumerate(lines[1:5]):
                                if ') ' in opt:
                                    letter, text = opt.split(') ', 1)
                                    options[letter] = text
                            
                            correct_answer = lines[5].split(': ')[1].strip() if ': ' in lines[5] else ''
                            
                            if (len(options) == 4 and 
                                all(key in options for key in ['A', 'B', 'C', 'D']) and 
                                correct_answer in ['A', 'B', 'C', 'D']):
                                
                                question = Question.objects.create(
                                    quiz=quiz,
                                    question_text=question_text,
                                    option_a=options['A'],
                                    option_b=options['B'],
                                    option_c=options['C'],
                                    option_d=options['D'],
                                    correct_answer=correct_answer
                                )
                                
                                # Add question data for response
                                questions_data.append({
                                    'id': question.id,
                                    'text': question_text,
                                    'options': [
                                        f"A) {options['A']}",
                                        f"B) {options['B']}",
                                        f"C) {options['C']}",
                                        f"D) {options['D']}"
                                    ]
                                })
                    except Exception as e:
                        print(f"Error parsing retry question: {str(e)}")
                        continue

            # Prepare the response
            response_data = {
                'id': story_instance.id,
                'title': story_instance.title,
                'story_text': pdf_text,
                'difficulty': difficulty,
                'questions': questions_data
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"Error generating questions: {str(e)}")
            raise serializers.ValidationError("Failed to generate quiz questions. Please try again.")

class QuizAttemptCreateView(generics.CreateAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class SubmitAnswerView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    video_processor = VideoProcessor()

    def post(self, request, attempt_id):
        try:
            attempt = QuizAttempt.objects.get(id=attempt_id, user=request.user)
            if attempt.completed:
                return Response(
                    {"error": "This quiz attempt has already been completed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            question_id = request.data.get('question_id')
            user_answer = request.data.get('answer')
            emotions = request.data.get('emotions', {})

            question = Question.objects.get(id=question_id, quiz=attempt.quiz)
            is_correct = user_answer.lower().strip() == question.correct_answer.lower().strip()

            Answer.objects.create(
                attempt=attempt,
                question=question,
                user_answer=user_answer,
                is_correct=is_correct
            )

            # Update emotions log
            current_emotions = attempt.emotions_log
            current_emotions[str(question_id)] = emotions
            attempt.emotions_log = current_emotions

            # Check if all questions are answered
            answered_questions = Answer.objects.filter(attempt=attempt).count()
            total_questions = Question.objects.filter(quiz=attempt.quiz).count()

            if answered_questions == total_questions:
                attempt.completed = True
                correct_answers = Answer.objects.filter(attempt=attempt, is_correct=True).count()
                attempt.score = (correct_answers / total_questions) * 100
                
                # Stop video processing and save emotion data
                self.video_processor.stop_capture()
                emotion_file = self.video_processor.save_emotion_data(attempt.id)
                if emotion_file:
                    attempt.emotion_data_file = emotion_file

            attempt.save()

            return Response({
                "is_correct": is_correct,
                "completed": attempt.completed,
                "score": attempt.score if attempt.completed else None
            })

        except QuizAttempt.DoesNotExist:
            return Response(
                {"error": "Quiz attempt not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Question.DoesNotExist:
            return Response(
                {"error": "Question not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def start_emotion_detection(self, attempt_id):
        """Start emotion detection in a separate thread"""
        try:
            self.video_processor.start_capture()
            
            def process_frames():
                while self.video_processor.is_processing:
                    self.video_processor.process_frame()
                    time.sleep(0.1)  # Process at ~10 FPS

            thread = threading.Thread(target=process_frames)
            thread.daemon = True
            thread.start()
            
            return True
        except Exception as e:
            print(f"Error starting emotion detection: {str(e)}")
            return False

class QuizAttemptDetailView(generics.RetrieveAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return QuizAttempt.objects.filter(user=self.request.user)

class UserQuizHistoryView(generics.ListAPIView):
    serializer_class = QuizAttemptSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return QuizAttempt.objects.filter(
            user=self.request.user,
            completed=True
        ).order_by('-completed_at')

class StartQuizAttemptView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    video_processor = VideoProcessor()

    def post(self, request, quiz_id):
        try:
            # Create new quiz attempt
            attempt = QuizAttempt.objects.create(
                user=request.user,
                quiz_id=quiz_id
            )

            # Start emotion detection
            if self.video_processor.start_emotion_detection(attempt.id):
                return Response({
                    "attempt_id": attempt.id,
                    "message": "Quiz attempt started with emotion detection"
                })
            else:
                return Response({
                    "attempt_id": attempt.id,
                    "message": "Quiz attempt started without emotion detection (camera unavailable)"
                })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class RegenerateQuizView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, story_id):
        try:
            story = Story.objects.get(id=story_id, user=request.user)
            
            # Generate new questions using Gemini AI
            model = genai.GenerativeModel('models/gemini-1.5-flash-8b-exp-0924')
            prompt = f"""Based on the following text, generate 5 {story.difficulty} level multiple-choice questions with answers.
            Format each question exactly as follows:
            Q1. [Question text]
            A) [Option A]
            B) [Option B]
            C) [Option C]
            D) [Option D]
            Answer: [Correct option letter]

            Text to analyze:
            {story.generated_story}"""
            
            response = model.generate_content(prompt)
            generated_content = response.text

            # Create new quiz
            quiz = Quiz.objects.create(
                story=story,
                title=f"Quiz for {story.title} ({story.difficulty.capitalize()} - Regenerated)"
            )

            # Parse and create questions
            questions = generated_content.split('\n\n')
            for q in questions:
                if q.strip().startswith('Q'):
                    lines = [line.strip() for line in q.split('\n') if line.strip()]
                    try:
                        if len(lines) >= 6:
                            question_text = lines[0].split('. ', 1)[1]
                            option_a = lines[1].split(') ', 1)[1] if len(lines[1].split(') ', 1)) > 1 else 'Option A'
                            option_b = lines[2].split(') ', 1)[1] if len(lines[2].split(') ', 1)) > 1 else 'Option B'
                            option_c = lines[3].split(') ', 1)[1] if len(lines[3].split(') ', 1)) > 1 else 'Option C'
                            option_d = lines[4].split(') ', 1)[1] if len(lines[4].split(') ', 1)) > 1 else 'Option D'
                            correct_answer = lines[5].split(': ')[1] if len(lines[5].split(': ')) > 1 else 'A'

                            Question.objects.create(
                                quiz=quiz,
                                question_text=question_text,
                                option_a=option_a,
                                option_b=option_b,
                                option_c=option_c,
                                option_d=option_d,
                                correct_answer=correct_answer
                            )
                    except (IndexError, ValueError) as e:
                        print(f"Error parsing question: {e}")
                        continue

            return Response({
                "message": "Quiz regenerated successfully",
                "quiz_id": quiz.id
            })

        except Story.DoesNotExist:
            return Response(
                {"error": "Story not found"},
                status=status.HTTP_404_NOT_FOUND
            )

class UserPointsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        points_obj, created = Points.objects.get_or_create(user=request.user)
        serializer = PointsSerializer(points_obj)
        return Response(serializer.data)

class LeaderboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        top_users = Points.objects.all().order_by('-total_points')[:10]
        serializer = PointsSerializer(top_users, many=True)
        return Response(serializer.data)
