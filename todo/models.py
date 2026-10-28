import os
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError



PRIORITY_LOW = 1
PRIORITY_MEDIUM = 2
PRIORITY_HIGH = 3

PRIORITY_CHOICES = [
	(PRIORITY_LOW, 'پایین'),
	(PRIORITY_MEDIUM, 'متوسط'),
	(PRIORITY_HIGH, 'بالا'),
]

STATUS_PENDING = 'pending'
STATUS_IN_PROGRESS = 'in_progress'
STATUS_DONE = 'done'

STATUS_CHOICES = [
	(STATUS_PENDING, 'در حال بررسی'),
	(STATUS_IN_PROGRESS, 'در حال انجام'),
	(STATUS_DONE, 'انجام شده'),
]

# ==========================================================
# UPLOAD HELPERS
# ==========================================================

def message_upload_path(instance, filename):
    """مسیر ذخیره‌سازی فایل پیوست پیام — با نام یونیک"""
    ext = os.path.splitext(filename)[1].lower()
    return f"chat/{instance.conversation_id}/{uuid.uuid4().hex}{ext}"


class TodoList(models.Model):
	owner = models.ForeignKey(User, on_delete=models.CASCADE)
	title = models.CharField(max_length = 255)
	priority = models.IntegerField(choices=PRIORITY_CHOICES,default=PRIORITY_MEDIUM)
	description = models.TextField(blank = True)
	due_date = models.DateTimeField(null= True, blank= True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	created_at = models.DateTimeField(auto_now_add = True)

	def __str__(self):
		return self.title
	

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)
	profile_image = models.ImageField(upload_to="profile_images/", blank=True)
	email= models.EmailField(blank=True)
	organizational_email= models.EmailField(blank=True)
	mobile = models.CharField(max_length=12, blank=True)
	internal_number = models.CharField(max_length=5, blank=True)
	bio = models.TextField(max_length=255, blank=True)


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name="conversations")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name="created_conversations")
    name = models.CharField(max_length=100, blank=True)
    is_group = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        if self.is_group and self.name:
            return self.name
        return f"گفتگو #{self.pk}"

    def clean(self):
        super().clean()
        if not self.is_group and self.pk:
            if self.participants.count() != 2:
                raise ValidationError("گفتگوی خصوصی باید دقیقاً دو شرکت‌کننده داشته باشد.")

    # ✅ save رو از داخل clean بیرون بیار
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="messages")
    text = models.TextField(blank=True)  # ← تغییر: blank=True
    reply_to = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="replies"
    )

    # ✅ فیلدهای جدید
    attachment = models.FileField(upload_to=message_upload_path, blank=True, null=True)
    attachment_type = models.CharField(max_length=20, blank=True)
    attachment_name = models.CharField(max_length=255, blank=True)
    attachment_size = models.BigIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    edited_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.sender.username}: {(self.text[:30] if self.text else '[فایل]')}"
    
class ConversationRead(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE,
        related_name="read_states"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="conversation_read_states"
    )
    last_read_message_id = models.IntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("conversation", "user")
        ordering = ["-updated_at"]