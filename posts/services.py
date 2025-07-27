import os
import google.generativeai as genai
from django.conf import settings
from .models import Tag, PostTag

def initialize_gemini():
    genai.configure(api_key=settings.GEMINI_API_KEY)
    return genai.GenerativeModel('gemini-pro-vision')

def extract_tags_from_post(content, image_path=None):
    model = initialize_gemini()
    
    prompt = """
    Analyze the following post content and extract relevant academic tags.
    Consider the subject area, topics, and concepts mentioned.
    Return the tags in the format: "tag1, tag2, tag3"
    Each tag should be a specific academic subject or topic.
    """
    
    if image_path and os.path.exists(image_path):
        image_parts = [{"mime_type": "image/jpeg", "data": open(image_path, "rb").read()}]
        response = model.generate_content([prompt, content, *image_parts])
    else:
        response = model.generate_content([prompt, content])
    
    tags_text = response.text.strip()
    tags = [tag.strip() for tag in tags_text.split(',')]
    
    return tags

def create_or_get_tags(tag_names):
    tags = []
    for name in tag_names:
        tag, created = Tag.objects.get_or_create(
            name=name,
            defaults={'category': 'Academic'}  # You can improve category detection later
        )
        tags.append(tag)
    return tags

def update_user_interests(user, tags, interaction_type='view'):
    """
    Update user interests based on their interaction with tagged content
    interaction_type can be 'view', 'like', 'comment', etc.
    """
    score_increment = {
        'view': 0.1,
        'like': 0.3,
        'comment': 0.5,
        'create': 1.0
    }.get(interaction_type, 0.1)
    
    for tag in tags:
        interest, created = UserInterest.objects.get_or_create(
            user=user,
            tag=tag,
            defaults={'score': score_increment}
        )
        if not created:
            interest.score += score_increment
            interest.save()

def get_recommended_posts(user, limit=10):
    """
    Get posts recommended for a user based on their interests
    """
    # Get user's top interests
    user_interests = UserInterest.objects.filter(user=user).order_by('-score')[:5]
    interest_tags = [interest.tag for interest in user_interests]
    
    # Get posts with matching tags
    recommended_posts = Post.objects.filter(
        tags__in=interest_tags
    ).distinct().order_by('-created_at')[:limit]
    
    return recommended_posts 