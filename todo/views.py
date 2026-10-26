import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .models import TodoList, UserProfile
from .forms import TodoForm, UserForm, UserProfileForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView
from django.urls import reverse_lazy


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
        profile,_ = UserProfile.objects.get_or_create(user=self.request.user)
        context["profile"]= profile
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