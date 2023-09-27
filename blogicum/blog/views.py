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


def get_ordered_posts_comments_count():
    '''Функция для сортировки постов по дате с количеством комментариев.'''
    return Post.objects.select_related(
        'author',
        'location',
        'category',
    ).annotate(
        comment_count=Count('comments')
    ).order_by('-pub_date')


def get_published_posts():
    '''Возвращает опубликованные посты и датой не позднее нынешней.'''
    return get_ordered_posts_comments_count().filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now(),
    )


class PostListView(ListView):
    '''CBV для главной страницы с постами.'''
    model = Post
    template_name = 'blog/index.html'
    paginate_by = POSTS_COUNT

    def __init__(self):
        self.queryset = get_published_posts()


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
            not self.object.category.is_published
            or not self.object.is_published
            or self.object.pub_date > timezone.now()
        ):
            raise Http404
        return super().dispatch(request, *args, **kwargs)

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
        self.category = get_object_or_404(
            Category.objects.filter(is_published=True),
            slug=self.kwargs['category_slug'],
        )
        return get_published_posts().filter(
            category=self.category,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class ProfileRedirectMixin:
    '''Миксин для перехода на страницу профиля.'''
    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
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
    LoginRequiredMixin,
    ValidationMixin,
    ProfileRedirectMixin,
    CreateView,
):
    '''CBV для создания коментария.'''
    template_name = 'blog/create.html'
    form_class = PostForm


class PostUpdateView(
    ContetnAuthorMixin,
    PostRedirectMixin,
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
        return get_ordered_posts_comments_count().filter(author=self.author)

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
            get_published_posts(),
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
