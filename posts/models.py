from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    text = models.TextField(verbose_name="Текст поста",
                            help_text="Соблюдайте правила "
                                      "орфографии и пунктуации")
    pub_date = models.DateTimeField(auto_now_add=True, db_index=True,
                                    verbose_name="Дата публикации")
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE, 
                               related_name="posts", verbose_name="Автор")
    group = models.ForeignKey('Group', on_delete=models.CASCADE, 
                              related_name="posts", blank=True, null=True, 
                              verbose_name="Сообщество",
                              help_text="Выберите сообщество в выпадающем "
                                        "списке, или оставте это поле пустым")
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    class Meta:
        verbose_name = "Пост"
        verbose_name_plural = "Посты"
        ordering = ["-pub_date"]

    def __str__(self):
        return self.text


class Group(models.Model):
    title = models.CharField(max_length=200, 
                             verbose_name="Название сообщества")
    slug = models.SlugField(unique=True, verbose_name="Адрес")
    description = models.TextField(verbose_name="Краткое описание")

    class Meta:
        verbose_name = "Сообщество"
        verbose_name_plural = "Сообщества"
        ordering = ["title"]

    def __str__(self):
        return self.title


class Comment(models.Model):
    post = models.ForeignKey(Post, null=True, on_delete=models.CASCADE, related_name="comments", verbose_name="Пост")
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="comments", verbose_name="Автор")
    text = models.TextField(verbose_name="Текст комментария", help_text="Соблюдайте правила орфографии и пунктуации")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата публикации")

    class Meta:
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"
        ordering = ["created"]

    def __str__(self):
        return self.text


class Follow(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="follower", verbose_name="Подписчик")
    author = models.ForeignKey(User, null=True, on_delete=models.CASCADE, related_name="following", verbose_name="Автор")

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ["author"]

    def __str__(self):
        return f"{self.user} подписан на {self.author}"

