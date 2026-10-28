import json, os
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import TodoList, UserProfile, Conversation, Message, ConversationRead
from .forms import TodoForm, UserForm, UserProfileForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Max, Count


# STATUS_CHOICES=['pending', 'in_progress', 'done']
# @login_required
# def todo_view(request):
# 	all_list=TodoList.objects.filter(owner=request.user)
# 	grouped_todos={
# 		status: all_list.filter(status=status)
# 				for status in STATUS_CHOICES
# 	}
# 	context={
# 		'grouped_todos': grouped_todos
# 	}
# 	return render(request, 'todo/index.html', context)


STATUS_CHOICES=['pending', 'in_progress', 'done']
class TodoListView(LoginRequiredMixin, ListView):
    model = TodoList
    template_name = "todo/index.html"
    context_object_name = "tasks"

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = context["tasks"]

        context["grouped_todos"] = {
            status: tasks.filter(status=status) for status in STATUS_CHOICES
        }

        context["stats"] = {
            "total":       tasks.count(),
            "pending":     tasks.filter(status="pending").count(),
            "in_progress": tasks.filter(status="in_progress").count(),
            "done":        tasks.filter(status="done").count(),
        }
        return context


# @login_required
# def creat_task_view(request):
# 	if request.method=="POST":
# 		form=TodoForm(request.POST)
# 		if form.is_valid():
# 			task = form.save(commit=False)
# 			task.owner = request.user
# 			task.save()
# 			messages.success(request, "وظیفه جدید با موفقیت ایجاد شد.")
# 			return redirect('todos')
# 	else:
# 		form=TodoForm()
# 	context={
# 		"form":form
# 	}
# 	return render(request, 'todo/creat_task.html', context)


class CreateTaskView(LoginRequiredMixin, CreateView):
	model= TodoList
	form_class= TodoForm
	template_name='todo/create_task.html'
	success_url= reverse_lazy("todos")

	def form_valid(self, form):
		form.instance.owner=self.request.user
		return super().form_valid(form)


# def delete_task_view(request, id):
# 	task=get_object_or_404(TodoList,owner=request.user, id= id)
# 	task.delete()
# 	messages.success(request, "وظیفه مورد نظر شما با موفقیت حذف شد.")
# 	return redirect('todos')

class DeleteTaskView(LoginRequiredMixin, DeleteView):
    model = TodoList
    template_name = "todo/todolist_confirm_delete.html"

    def get_queryset(self):
        return TodoList.objects.filter(
            owner=self.request.user
        )

    def get_success_url(self):
        return reverse_lazy("todos")



# def edit_task_view(request, id):
# 	task=get_object_or_404(TodoList,owner=request.user, id= id)
# 	if request.method=="POST":
# 		form=TodoForm(request.POST, instance=task)
# 		if form.is_valid():
# 			form.save()
# 			messages.success(request, "وظیفه مورد نظر شما با موفقیت ویرایش شد.")	
# 			return redirect('todos')
# 	else:
# 		form=TodoForm(instance=task)
# 	context={
# 		"form":form
# 	}
# 	return render(request, 'todo/edit_task.html', context)

class UpdateTaskView(LoginRequiredMixin, UpdateView):
	model=TodoList
	form_class=TodoForm
	template_name="todo/edit_task.html"
            
	def get_queryset(self):
		return TodoList.objects.filter(owner=self.request.user)
	
	def get_success_url(self):
		return reverse_lazy("todos")


def login_view(request):
	if request.method == "POST":
		username = request.POST.get("username")
		password = request.POST.get("password")

		user = authenticate(request, username=username, password=password)

		if user is not None:
			login(request, user)
			return redirect("todos")
		else:
			return render(request, "todo/login.html", {"error": "اطلاعات وارد شده صحیح نمی باشد"})
	return render(request, "todo/login.html")


def logout_view(request):
	logout(request)
	return redirect("login")


def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            return render(
                request,
                "todo/register.html",
                {"error": "رمز عبور و تکرار آن مطابقت ندارند"}
            )

        if len(password) < 8:
            return render(
                request,
                "todo/register.html",
                {"error": "رمز عبور باید حداقل ۸ کاراکتر باشد"}
            )

        # بررسی تکراری بودن Username
        if User.objects.filter(username=username).exists():
            return render(
                request,
                "todo/register.html",
                {"error": "این نام کاربری قبلاً ثبت شده است."}
            )

        user = User.objects.create_user(
            username=username,
            password=password,
        )
        UserProfile.objects.create(user=user)

        login(request, user)
        return redirect("todos")

    return render(request, "todo/register.html")


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "todo/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        context["profile"] = profile

        tasks = TodoList.objects.filter(owner=self.request.user)
        context["user_stats"] = {
            "total":   tasks.count(),
            "done":    tasks.filter(status="done").count(),
            "pending": tasks.filter(status="pending").count(),
        }
        return context
    

class EditProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserForm
    profile_form_class = UserProfileForm
    template_name = "todo/edit_profile.html"

    def get_queryset(self):
        return User.objects.filter(pk=self.request.user.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = UserProfile.objects.get(user=self.request.user)
        profile_form = kwargs.get("profile_form")
        if profile_form is None:
            profile_form = self.profile_form_class(instance=profile)
        context["profile_form"] = profile_form
        return context

    def form_valid(self, form):
        profile_form = self.profile_form_class(
            self.request.POST,
            self.request.FILES,
            instance=self.request.user.userprofile)
        
        if not profile_form.is_valid():
            context = self.get_context_data(form=form,profile_form=profile_form)
            return self.render_to_response(context)
        profile_form.save()

        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy("profile")


class UsersListView(LoginRequiredMixin, ListView):
     model= User
     template_name= "todo/users.html"

     def get_queryset(self):
          return User.objects.exclude(pk=self.request.user.pk)
     

class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = "todo/user_detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # ✅ پروفایل رو خودکار بساز اگه نیست
        UserProfile.objects.get_or_create(user=obj)
        return obj
    
    
@login_required
def update_task_status(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)

    task = get_object_or_404(TodoList, pk=pk, owner=request.user)

    try:
        data = json.loads(request.body)
        new_status = data.get("status")
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    valid = [s[0] for s in STATUS_CHOICES]
    if new_status not in valid:
        return JsonResponse({"ok": False, "error": "Invalid status"}, status=400)

    task.status = new_status
    task.save(update_fields=["status"])
    return JsonResponse({"ok": True, "status": new_status})

# ==========================================================
# CHAT
# ==========================================================

class ConversationListView(LoginRequiredMixin, ListView):
    model = Conversation
    template_name = "todo/chat/conversation_list.html"
    context_object_name = "conversations"

    def get_queryset(self):
        return (
            Conversation.objects
            .filter(participants=self.request.user)
            .annotate(last_message_at=Max("messages__created_at"))
            .order_by("-last_message_at", "-updated_at")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        enriched = []
        for conv in context["conversations"]:
            # نام نمایشی
            if conv.is_group and conv.name:
                display_name = conv.name
            else:
                others = conv.participants.exclude(pk=self.request.user.pk)
                if others.exists():
                    o = others.first()
                    display_name = o.get_full_name() or o.username
                else:
                    display_name = "گفتگوی شخصی"

            # آخرین پیام
            last_msg = conv.messages.order_by("-created_at").first()

            # تعداد خوانده‌نشده
            read = ConversationRead.objects.filter(
                conversation=conv, user=self.request.user
            ).first()
            last_id = read.last_read_message_id if read else 0
            unread = conv.messages.filter(id__gt=last_id).exclude(
                sender=self.request.user
            ).count()

            enriched.append({
                "conv": conv,
                "display_name": display_name,
                "other": conv.participants.exclude(pk=self.request.user.pk).first(),
                "last_message": last_msg,
                "unread": unread,
            })

        context["enriched"] = enriched
        return context

class ConversationDetailView(LoginRequiredMixin, DetailView):
    model = Conversation
    template_name = "todo/chat/conversation_detail.html"
    context_object_name = "conversation"

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user)

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # علامت‌گذاری پیام‌ها به عنوان خوانده‌شده
        self._mark_as_read(obj)
        return obj

    def _mark_as_read(self, conv):
        last_msg = conv.messages.order_by("-id").first()
        if not last_msg:
            return
        read, _ = ConversationRead.objects.get_or_create(
            conversation=conv, user=self.request.user
        )
        if last_msg.id > read.last_read_message_id:
            read.last_read_message_id = last_msg.id
            read.save(update_fields=["last_read_message_id", "updated_at"])

    def _get_display_name(self, conv):
        """محاسبه نام نمایشی گفتگو برای کاربر فعلی"""
        if conv.is_group and conv.name:
            return conv.name
        others = conv.participants.exclude(pk=self.request.user.pk)
        if others.exists():
            other = others.first()
            return other.get_full_name() or other.username
        return "گفتگوی شخصی"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conv = self.object

        # نمایش نام و طرف مقابل
        others = conv.participants.exclude(pk=self.request.user.pk)
        context["display_name"] = self._get_display_name(conv)
        context["other_user"] = others.first() if others.exists() else None

        # لیست پیام‌ها
        context["messages_list"] = (
            conv.messages
            .select_related("sender")
            .order_by("created_at")
        )

        # لیست همه گفتگوها برای سایدبار
        convs = (
            Conversation.objects
            .filter(participants=self.request.user)
            .annotate(last_message_at=Max("messages__created_at"))
            .order_by("-last_message_at", "-updated_at")
        )

        enriched = []
        for c in convs:
            # نام نمایشی
            if c.is_group and c.name:
                name = c.name
            else:
                o = c.participants.exclude(pk=self.request.user.pk).first()
                name = (o.get_full_name() or o.username) if o else "گفتگو"

            # آخرین پیام
            last = c.messages.order_by("-created_at").first()

            # تعداد خوانده‌نشده
            read = ConversationRead.objects.filter(
                conversation=c, user=self.request.user
            ).first()
            last_id = read.last_read_message_id if read else 0
            unread = c.messages.filter(id__gt=last_id).exclude(
                sender=self.request.user
            ).count()

            enriched.append({
                "conv": c,
                "display_name": name,
                "last_message": last,
                "unread": unread,
            })

        context["all_conversations"] = enriched
        return context

@login_required
def start_conversation_view(request, user_id):
    other_user = get_object_or_404(User, pk=user_id)

    if other_user == request.user:
        messages.error(request, "نمی‌توانید با خودتان گفتگو کنید.")
        return redirect("users")

    existing = (
        Conversation.objects
        .filter(is_group=False, participants=request.user)
        .filter(participants=other_user)
        .first()
    )
    if existing:
        return redirect("conversation_detail", pk=existing.pk)

    conv = Conversation.objects.create(is_group=False, created_by=request.user)
    conv.participants.add(request.user, other_user)
    return redirect("conversation_detail", pk=conv.pk)


@login_required
def send_message_view(request, pk):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed"}, status=405)

    conv = get_object_or_404(Conversation, pk=pk, participants=request.user)

    # ─── تشخیص نوع درخواست (JSON یا multipart) ───
    is_multipart = request.content_type and request.content_type.startswith("multipart/")

    if is_multipart:
        text = (request.POST.get("text") or "").strip()
        attachment = request.FILES.get("attachment")
    else:
        try:
            data = json.loads(request.body)
            text = (data.get("text") or "").strip()
            attachment = None
        except (json.JSONDecodeError, AttributeError):
            return JsonResponse({"ok": False, "error": "داده نامعتبر"}, status=400)

    if not text and not attachment:
        return JsonResponse({"ok": False, "error": "پیام خالی است"}, status=400)

    # ─── اعتبارسنجی فایل ───
    atype = ""
    if attachment:
        MAX_SIZE = 50 * 1024 * 1024  # 50MB
        if attachment.size > MAX_SIZE:
            return JsonResponse(
                {"ok": False, "error": "حجم فایل بیش از ۵۰ مگابایت است"}, status=400
            )

        FORBIDDEN = {".exe", ".bat", ".cmd", ".sh", ".php", ".js", ".jsp", ".asp", ".aspx"}
        ext = os.path.splitext(attachment.name)[1].lower()
        if ext in FORBIDDEN:
            return JsonResponse({"ok": False, "error": "این نوع فایل مجاز نیست"}, status=400)

        mime = attachment.content_type or ""
        if mime.startswith("image/"):
            atype = "image"
        elif mime.startswith("video/"):
            atype = "video"
        elif mime.startswith("audio/"):
            atype = "audio"
        else:
            atype = "file"

    # ─── ساخت پیام ───
    msg = Message(
        conversation=conv,
        sender=request.user,
        text=text,
        attachment_type=atype,
    )
    if attachment:
        msg.attachment = attachment
        msg.attachment_name = attachment.name
        msg.attachment_size = attachment.size

    msg.save()
    conv.save()  # updated_at

    # ─── پاسخ ───
    msg_data = {
        "id": msg.id,
        "text": msg.text,
        "sender": msg.sender.username,
        "sender_name": msg.sender.get_full_name() or msg.sender.username,
        "sender_id": msg.sender.id,
        "is_own": True,
        "created_at": msg.created_at.strftime("%H:%M"),
        "attachment": None,
    }
    if msg.attachment:
        msg_data["attachment"] = {
            "url": msg.attachment.url,
            "type": msg.attachment_type,
            "name": msg.attachment_name,
            "size": msg.attachment_size,
        }

    return JsonResponse({"ok": True, "message": msg_data})


@login_required
def fetch_messages_view(request, pk):
    conv = get_object_or_404(Conversation, pk=pk, participants=request.user)
    try:
        after_id = int(request.GET.get("after", 0) or 0)
    except ValueError:
        after_id = 0

    msgs = (
        conv.messages
        .filter(id__gt=after_id)
        .select_related("sender")
        .order_by("created_at")
    )

    result = []
    for m in msgs:
        item = {
            "id": m.id,
            "text": m.text,
            "sender": m.sender.username,
            "sender_name": m.sender.get_full_name() or m.sender.username,
            "sender_id": m.sender.id,
            "is_own": m.sender_id == request.user.id,
            "created_at": m.created_at.strftime("%H:%M"),
            "attachment": None,
        }
        if m.attachment:
            item["attachment"] = {
                "url": m.attachment.url,
                "type": m.attachment_type,
                "name": m.attachment_name,
                "size": m.attachment_size,
            }
        result.append(item)

    # mark as read
    last_msg = conv.messages.order_by("-id").first()
    if last_msg:
        read, _ = ConversationRead.objects.get_or_create(
            conversation=conv, user=request.user
        )
        if last_msg.id > read.last_read_message_id:
            read.last_read_message_id = last_msg.id
            read.save(update_fields=["last_read_message_id", "updated_at"])

    return JsonResponse({"ok": True, "messages": result})
    
@login_required
def unread_count_view(request):
    """تعداد کل پیام‌های خوانده‌نشده کاربر در همه گفتگوها"""
    convs = Conversation.objects.filter(participants=request.user)
    total = 0
    details = []

    for conv in convs:
        read = ConversationRead.objects.filter(
            conversation=conv, user=request.user
        ).first()
        last_id = read.last_read_message_id if read else 0

        unread_qs = conv.messages.filter(id__gt=last_id).exclude(sender=request.user)
        count = unread_qs.count()

        if count > 0:
            total += count
            last = unread_qs.order_by("-created_at").first()

            # نام نمایشی
            if conv.is_group and conv.name:
                name = conv.name
            else:
                others = conv.participants.exclude(pk=request.user.pk)
                if others.exists():
                    o = others.first()
                    name = o.get_full_name() or o.username
                else:
                    name = "گفتگو"

            details.append({
                "conversation_id": conv.pk,
                "conversation_name": name,
                "count": count,
                "last_text": last.text[:60] if last else "",
                "last_sender": (last.sender.get_full_name() or last.sender.username) if last else "",
            })

    return JsonResponse({"ok": True, "total": total, "details": details})