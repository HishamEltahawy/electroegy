import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db.models import Avg

# Create your models here.
class Categories(models.TextChoices):
    COMPUTER = 'Computer'
    FOOD = 'Food'
    KIDS = 'Kids'
    HOME = 'Home'

class Products(models.Model):
    id = models.UUIDField(
    primary_key=True,
    default=uuid.uuid4,
    editable=False
    )
    name = models.CharField(max_length=200, default='', blank=False)
    image = models.ImageField(blank=True, null=True, upload_to='ProductsApp/images/%Y/%m/%d/')
    description = models.TextField(max_length=1000, default='', blank=False)
    price = models.DecimalField(max_digits=7, decimal_places=2, null=False, default=0.00)
    brand = models.CharField(max_length=200, default='', blank=False)
    category = models.CharField(max_length=50, choices=Categories.choices)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    stock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review_count = models.IntegerField(default=0, blank=True, null=True)  # عدد المراجعات
    def __str__(self):
        return self.name
    
class Reviews(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(max_length=1000, default='', blank=False)
    rating = models.IntegerField(
        default=0,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # منع المراجعات المكررة

    def __str__(self):
        return f"{self.user.username} - {self.product.name} - {self.rating}"

@receiver(post_save, sender=Reviews)
@receiver(post_delete, sender=Reviews)
def update_product_rating(sender, instance, **kwargs):
    product = instance.product
    reviews = product.reviews.all()
    if reviews.exists():
        product.rating = reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
    else:
        product.rating = 0  # إذا لم تكن هناك مراجعات
    product.save()
    
@receiver(post_save, sender=Reviews)
@receiver(post_delete, sender=Reviews)
def update_review_count(sender, instance, **kwargs):
    product = instance.product
    product.review_count = product.reviews.count()
    product.save()