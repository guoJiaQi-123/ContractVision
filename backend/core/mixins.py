from django.db import models
from django.utils import timezone


class SoftDeleteQuerySet(models.QuerySet):

    def delete(self):
        return self.update(is_deleted=True, updated_at=timezone.now())

    def hard_delete(self):
        return super().delete()

    def alive(self):
        return self.filter(is_deleted=False)

    def dead(self):
        return self.filter(is_deleted=True)


class SoftDeleteManager(models.Manager):

    def get_queryset(self):
        return SoftDeleteQuerySet(self.model, using=self._db).alive()

    def all_with_deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db)

    def deleted(self):
        return SoftDeleteQuerySet(self.model, using=self._db).dead()


class SoftDeleteMixin(models.Model):
    is_deleted = models.BooleanField(default=False, db_index=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.save(update_fields=['is_deleted'])

    def hard_delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_deleted = False
        self.save(update_fields=['is_deleted'])


class TimeStampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
