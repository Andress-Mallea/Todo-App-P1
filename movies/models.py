from django.db import models

class Todo(models.Model):
    title = models.CharField('title', max_length=200)
    description = models.TextField('description', blank=True, null=True)
    completed = models.BooleanField('completed', default=False)
    created_at = models.DateTimeField('created_at', auto_now_add=True)

    class Meta:
        db_table = 'todos' # Debe coincidir con la tabla que creó Flask
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return self.title