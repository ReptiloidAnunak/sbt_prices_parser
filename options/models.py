from django.db import models


class Options(models.Model):

    class Meta:
        verbose_name = "Настройка"
        verbose_name_plural = "Настройки"

    dollar_rate = models.FloatField(default=1400)

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj