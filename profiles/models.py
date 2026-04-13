from django.conf import settings
from django.db import models


class Profile(models.Model):
    """User profile model - created automatically via post_save signal on User."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='usuário',
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='telefone',
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        blank=True,
        verbose_name='avatar',
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='criado em')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='atualizado em')

    class Meta:
        ordering = ('user__email',)
        verbose_name = 'perfil'
        verbose_name_plural = 'perfis'

    def __str__(self):
        return self.user.email
