from django.db import models

# Create your models here.
from django.db import models

from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    # ✅ Add this field to store default attributes
    default_attributes = models.JSONField(
        default=list,
        blank=True,
        help_text="List of default attribute names for this category, e.g., ['Size', 'Color']"
    )

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Attribute(models.Model):
    """ e.g., 'Size', 'Color', 'Weight', 'Material' """
    name = models.CharField(max_length=100, unique=True)
    # This links an attribute to one or more categories
    categories = models.ManyToManyField(Category, related_name='attributes')

    def __str__(self):
        return self.name