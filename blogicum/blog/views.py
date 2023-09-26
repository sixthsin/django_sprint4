from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from .forms import CommentForm, PostForm
from .models import Category, Comment, Post, User

POSTS_COUNT = 10


def get_filtered_posts():
    '''Функция для фильтрации постов с количеством комментариев.'''
    return Post.objects.select_related(
        'author',
        'location',
        'category',
    ).filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True,
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def post_queryset():
    '''Возвращает QuerySet из модели с постами'''
    return Post.objects.select_related(
        'author',
        'location',
        'category',
    ).filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    ).order_by('-pub_date')


class PostListView(ListView):
    '''CBV для главной страницы с постами.'''
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_COUNT

    def get_queryset(self):
        return get_filtered_posts()


class ContetnAuthorMixin(LoginRequiredMixin):
    '''Миксин проверки является ли пользователь автором.'''
    def dispatch(self, request, *args, **kwargs):
        if self.get_object().author != request.user:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs['post_id']
            )
        return super().dispatch(request, *args, **kwargs)


class PostDetailView(DetailView):
    '''CBV для подробной страницы поста.'''
    model = Post
    template_name = 'blog/detail.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author != self.request.user and (
            self.object.category.is_published is False
            or self.object.is_published is False
            or self.object.pub_date > timezone.now()
        ):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return super().get_queryset().select_related(
            'author',
            'location',
            'category',
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.select_related(
            'author'
        )
        return context


class CategoryListView(ListView):
    '''CBV для страницы категории поста.'''
    paginate_by = POSTS_COUNT
    template_name = 'blog/category.html'

    def get_queryset(self):
        return get_filtered_posts().filter(
            category__slug=self.kwargs['category_slug'],
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            is_published=True,
            slug=self.kwargs['category_slug'],
        )
        return context


class ProfileRedirectMixin:
    '''Миксин для перехода на страницу профиля.'''
    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user}
        )


class PostRedirectMixin:
    '''Миксин для перехода на страницу поста.'''
    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class ValidationMixin:
    '''Миксин-валидатор чтоб задать пользователя как автора.'''
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostCreateView(
    ValidationMixin,
    LoginRequiredMixin,
    ProfileRedirectMixin,
    CreateView,
):
    '''CBV для создания коментария.'''
    template_name = 'blog/create.html'
    form_class = PostForm


class PostUpdateView(
    ContetnAuthorMixin,
    LoginRequiredMixin,
    PostRedirectMixin,
    ValidationMixin,
    UpdateView,
):
    '''CBV для редактирования поста.'''
    model = Post
    template_name = 'blog/create.html'
    form_class = PostForm
    pk_url_kwarg = 'post_id'


class PostDeleteView(
    ContetnAuthorMixin,
    ProfileRedirectMixin,
    ValidationMixin,
    DeleteView,
):
    '''CBV для удаления поста.'''
    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = PostForm(instance=self.object)
        return context


class ProfileListView(ListView):
    '''CBV для страницы профиля.'''
    template_name = 'blog/profile.html'
    model = Post
    paginate_by = POSTS_COUNT

    def get_queryset(self):
        self.author = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return Post.objects.select_related(
            'author',
            'location',
            'category',
        ).filter(
            author=self.author
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.author
        return context


class ProfileUpdateView(LoginRequiredMixin, ProfileRedirectMixin, UpdateView):
    '''CBV для редактирования профиля.'''
    model = User
    template_name = 'blog/user.html'
    fields = (
        'username',
        'first_name',
        'last_name',
        'email',
    )

    def get_object(self, queryset=None):
        return self.request.user


class CommentMixin(PostRedirectMixin):
    '''Миксин для коментов.'''
    model = Comment
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'comment_id'


class CommentCreateView(LoginRequiredMixin, CommentMixin, CreateView):
    '''CBV для создания коментария.'''
    form_class = CommentForm

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.post = get_object_or_404(
            get_filtered_posts(),
            pk=self.kwargs['post_id']
        )
        return super().form_valid(form)


class CommentUpdateView(
    CommentMixin,
    ContetnAuthorMixin,
    PostRedirectMixin,
    UpdateView,
):
    '''CBV для редактирования коментария.'''
    form_class = CommentForm


class CommentDeleteView(
    CommentMixin,
    ContetnAuthorMixin,
    PostRedirectMixin,
    DeleteView,
):
    '''CBV для удаления коментария.'''
    ...
