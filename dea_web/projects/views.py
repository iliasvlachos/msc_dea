from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from .models import Project, File, FileResult
from django.urls import reverse
from users.models import UserTier
from .utils import getFileColumns, getFileRows, pulp_solve
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .mixins import TierRequiredMixin


# Create your views here.
def index(request):
    return render(request, '../templates/index.html')


def home(request):
    return render(request, 'projects/index.html')


class ProjectCreateView(LoginRequiredMixin, TierRequiredMixin, UserPassesTestMixin, CreateView):
    model = Project
    fields = ['title', 'description']

    def test_func(self):
        user = self.request.user
        user_tier = UserTier.objects.filter(user=user).first()
        projects = Project.objects.filter(user=user).count()
        if projects >= user_tier.tier.max_projects:
            return False
        else:
            return True

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Project

    def test_func(self):
        project = self.get_object()
        if self.request.user == project.user:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["files_list"] = File.objects.filter(project=self.get_object())
        return context


class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Project
    fields = ['title', 'description']
    template_name = 'projects/project_update_form.html'

    def test_func(self):
        project = self.get_object()
        if self.request.user == project.user:
            return True
        return False


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Project

    def test_func(self):
        project = self.get_object()
        user = self.request.user
        if project.user == user:
            return True
        return False

    def get_success_url(self):
        return reverse('projects-list')


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(user=self.request.user)


class ProjectFileCreateView(LoginRequiredMixin, CreateView):
    model = File
    fields = ['name', 'description', 'file']

    def form_valid(self, form):
        project = Project.objects.get(pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.user = self.request.user
        return super().form_valid(form)


class ProjectFileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    template_name = "files/project_file_update.html"
    model = File
    fields = ['name', 'description', 'file']

    def test_func(self):
        file = self.get_object()
        user = self.request.user
        if file.user == user:
            return True
        return False

    def form_valid(self, form):
        project = Project.objects.get(pk=self.kwargs['pk'])
        form.instance.project = project
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["file"] = self.get_object()
        return context

    def get_object(self):
        return File.objects.get(pk=self.kwargs['fi'])


class ProjectFileDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = File
    template_name = "files/project_file_detail.html"
    context_object_name = 'file'

    def test_func(self):
        file = self.get_object()
        user = self.request.user
        if file.user == user:
            return True
        return False

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = Project.objects.get(id=self.kwargs['pk'])
        return context

    def get_object(self):
        return File.objects.get(pk=self.kwargs['fi'])


class ProjectFileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = File

    def test_func(self):
        file = self.get_object()
        user = self.request.user
        if file.user == user:
            return True
        return False

    def get_object(self):
        return File.objects.get(pk=self.kwargs['fi'])

    def get_success_url(self):
        return reverse('projects-detail', kwargs={'pk': self.kwargs['pk']})


class FileResultDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = FileResult
    template_name = "file_result/file_result_detail.html"
    context_object_name = 'file_result'

    def test_func(self):
        file_result = self.get_object()
        user = self.request.user
        if file_result.file.user == user:
            return True
        return False

    def get_object(self):
        return FileResult.objects.get(pk=self.kwargs['res'])


@login_required
def lp_solve(request, pk, fi):
    if request.method == 'POST':
        project_file = File.objects.get(pk=fi)
        names = getFileColumns(project_file.file.path).keys()
        inputs = []
        outputs = []
        orientation = request.POST.get('minmax')
        for name in names:
            if request.POST.get(name + '_input') == '1':
                inputs.append(name)
            else:
                outputs.append(name)
        if orientation == 'input':
            minmax = 'Max'
        else:
            minmax = 'Min'
        rts = request.POST.get('rts')
        result_data = pulp_solve(project_file, inputs, outputs, minmax, rts)
        context = {
            'result_data': result_data
        }
        return render(request, 'file_result/pulp_result_data.html', context)
    else:
        project_file = File.objects.get(pk=fi)
        if project_file.user != request.user:
            raise PermissionDenied()
        names = getFileColumns(project_file.file.path).keys()
        context = {
            'names': names,
            'file': project_file
        }
        return render(request, 'files/project_file_lp_solve.html', context)
