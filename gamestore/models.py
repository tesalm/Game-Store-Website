from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField


class RegUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    developer = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Tag(models.Model):
    """Tags that games belong to

    Tags have separate model so each game can have multiple ones.
    """
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Game(models.Model):
    name = models.CharField(max_length=50, unique=True)
    url = models.URLField(max_length=200, unique=True)
    # current price in store
    price = models.DecimalField(default=0, max_digits=8, decimal_places=2)

    logo = CloudinaryField("logo", blank=True, null=True)
    banner = CloudinaryField("banner", blank=True, null=True)
    description = models.TextField(max_length=1000, blank=True)

    developer = models.ForeignKey(RegUser, on_delete=models.CASCADE)
    tags = models.ManyToManyField(Tag, blank=True)

    def __str__(self):
        return self.name


class PurchasedGame(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    player = models.ForeignKey(RegUser, on_delete=models.CASCADE)
    game_state = models.CharField(max_length=10000, blank=True, default="")
    high_score = models.IntegerField(default=0)

    def __str__(self):
        return self.player.user.username+" - "+self.game.name


class GameReview(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    reviewer = models.ForeignKey(RegUser, on_delete=models.CASCADE)
    review_text = models.TextField(max_length=500, blank=True)
    review_star = models.IntegerField(default=0)


class GameSale(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    time_of_purchase = models.DateTimeField(auto_now_add=True)
    # even if the current price of a game changes this still stays the same
    # (useful for sales statistics)
    ref = models.IntegerField()
    pid = models.CharField(max_length=20)
    price_paid = models.DecimalField(default=0, max_digits=8, decimal_places=2)

    def __str__(self):
        return self.game.name+" - "+str(self.price_paid)+"€"
