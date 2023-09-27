from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
TITLE_MAX_LENGTH = NAME_MAX_LENGTH = 256
SELF_TITLE_LENGTH = SELF_NAME_LENGTH = 20
COMMENT_SELF_TEXT_LEN = 25


class BaseModel(models.Model):
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Добавлено'
    )

    class Meta:
        abstract = True


class Post(BaseModel):
    title = models.CharField(
        verbose_name='Заголовок',
        max_length=TITLE_MAX_LENGTH
    )
    text = models.TextField(verbose_name='Текст')
    pub_date = models.DateTimeField(
        verbose_name='Дата и время публикации',
        help_text=(
            'Если установить дату и время в '
            'будущем — можно делать отложенные публикации.'
        )
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации',
        related_name='posts',
    )
    location = models.ForeignKey(
        'Location',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name='Местоположение',
        related_name='posts',
    )
    category = models.ForeignKey(
        'Category',
        null=True,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        related_name='posts',
    )
    image = models.ImageField('Фото', upload_to='post_images', blank=True)
    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']

    def __str__(self):
        return self.title[:SELF_TITLE_LENGTH]


class Category(BaseModel):
    title = models.CharField(
        verbose_name='Заголовок',
        max_length=TITLE_MAX_LENGTH
    )
    description = models.TextField(verbose_name='Описание')
    slug = models.SlugField(
        verbose_name='Идентификатор',
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )
    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:SELF_TITLE_LENGTH]


class Location(BaseModel):
    name = models.CharField(
        verbose_name='Название места',
        max_length=NAME_MAX_LENGTH
    )
    is_published = models.BooleanField(
        verbose_name='Опубликовано',
        default=True,
        help_text='Снимите галочку, чтобы скрыть публикацию.'
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name[:SELF_NAME_LENGTH]


class Comment(BaseModel):
    text = models.TextField(
        verbose_name='Текст комментария',
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return f'{self.author}: {self.text[:COMMENT_SELF_TEXT_LEN]}'
