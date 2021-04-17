import json
import datetime
import os
from hashlib import md5

from django.shortcuts import render, redirect, get_object_or_404, render_to_response
from django.http import HttpResponseForbidden, HttpResponse, HttpResponseRedirect, JsonResponse
from django.views import View
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q # for search querys
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import ValidationError

from cloudinary.forms import cl_init_js_callbacks
from .forms import GameForm, RegisterForm
from gamestore.models import RegUser, Game, PurchasedGame, GameReview, GameSale
from gamestore.utils import *

from gamestore.tokens import account_activation_token
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string

PAYMENT_SID = os.environ["PAYMENT_SID"]
PAYMENT_SECRET = os.environ["PAYMENT_SECRET"]


# Public view
def index(request):
    context = dict(games=Game.objects.all())
    return render(request, "main.html", context)


@login_required(login_url='login')
def play(request, gid):
    uid = user_from_req(request).pk

    g = get_object_or_404(Game, pk=gid)
    if not PurchasedGame.objects.filter(player=uid, game=gid).exists():
        if g.price == 0:
            # Add PurchasedGame if game is not yet owned and price is 0
            p = get_object_or_404(RegUser, pk=uid)
            PurchasedGame.objects.create(player=p, game=g)
        else: 
            return redirect("purchase", gid=gid)

    pgame = get_object_or_404(PurchasedGame, player=uid, game=gid)
    scores = PurchasedGame.objects.filter(game=gid, high_score__gte=1)
    scores = scores.order_by("-high_score")[:10]
    context = dict(game=pgame.game, high_scores=scores)

    if request.method == "POST" and request.is_ajax:
        requestType = request.POST.get('type')
        if (requestType == "SCORE"):
            score = request.POST.get('score')

            if pgame.high_score < int(score):
                pgame.high_score = int(score)

            pgame.save()
            return HttpResponse(pgame.high_score)

        elif (requestType == "SAVE"):
            gameState = request.POST.get('gameState')
            pgame.game_state = gameState
            pgame.save()
            return JsonResponse({'success': 'success'})

        elif (requestType == "LOAD_REQUEST"):
            data = json.loads(request.POST.get('jsondata', None))
            if pgame.game_state:
                data["messageType"] = "LOAD"
                data["gameState"] = json.loads(pgame.game_state)
            else:
                data["messageType"] = "ERROR"
                data["message"] = "No gamestate to be loaded"

            json_state = json.dumps(data)
            return HttpResponse(json_state, content_type='application/json')

    return render(request, 'play.html', context)


class GameUploadView(LoginRequiredMixin, View):
    form_class = GameForm
    initial = {'price': 0}
    template_name = "gameupload.html"

    def get(self, request):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        user = user_from_req(request)

        form = self.form_class(request.POST, request.FILES)
        context = dict(form=form)
        context["posted"] = form.instance
        if form.is_valid():
            form.instance.developer = user
            uploaded = form.save()
            # add newly uploaded game to developer's collection
            PurchasedGame.objects.create(player=user, game=uploaded)
            # redirect to the newly created game's page
            return redirect("play", gid=uploaded.pk)
        return render(request, self.template_name, context)


@login_required(login_url='login')
def dashboard(request):
    user = user_from_req(request)

    boughtGames = PurchasedGame.objects.filter(player=user)
    context = dict(games=boughtGames)

    # Developer dashboard
    if user.developer and request.is_ajax:
        requestType = request.POST.get('type')
        if (requestType == "collection"):
            boughtGames = PurchasedGame.objects.filter(player=user)
            context = dict(games=boughtGames)
            return render(request, 'gamecollection.html', context)

        elif (requestType == "uploaded"):
            uploadedGames = Game.objects.filter(developer=user)
            sales = GameSale.objects.filter(game__in=uploadedGames)
            sales = sales.order_by("time_of_purchase")[:20]
            context = dict(games=uploadedGames, sales=sales)
            return render(request, 'developergames.html', context)

    return render(request, 'dashboard.html', context)


def search(request):
    if request.method == "POST":
        search_term = request.POST.get('search')

        # case-insensitive search for games/developers by name/tags
        result = Game.objects.filter(Q(name__icontains=search_term) |
                                     Q(developer__user__username__icontains=search_term) |
                                     Q(tags__name__icontains=search_term)).distinct()

        context = dict(games=result)
    return render(request, 'main.html', context)


@login_required(login_url='login')
def purchase(request, gid):
    game = Game.objects.get(pk=gid)

    # check if the user already owns the game
    if PurchasedGame.objects.filter(player=user_from_req(request), game=game).exists():
        messages.error(request, game.name+" is already in your collection!")
        return render(request, 'payment/error.html')

    pid = "%s_%s"%(request.user.id, game.id)
    action = "http://payments.webcourse.niksula.hut.fi/pay/"
    amount = game.price
    checksum_str = "pid={}&sid={}&amount={}&token={}".format(pid, PAYMENT_SID, amount, PAYMENT_SECRET)

    success_url = request.build_absolute_uri(reverse("payment_result"))
    cancel_url = request.build_absolute_uri(reverse("payment_result"))
    error_url = request.build_absolute_uri(reverse("payment_result"))

    m = md5(checksum_str.encode("ascii"))
    checksum = m.hexdigest()

    return render(request, 'payment/purchase.html', {'game': game, 'pid': pid, 
                  'sid': PAYMENT_SID, 'amount': amount, 'checksum': checksum, 'action': action, 
                  'success_url': success_url, 'cancel_url': cancel_url, 'error_url': error_url})


def payment_result(request):
    result = request.GET['result']
    pid = request.GET['pid']
    user_id, game_id = pid.split('_')
    ref = request.GET['ref']
    checksum_str = "pid={}&ref={}&result={}&token={}".format(pid, ref, result, PAYMENT_SECRET)
    got_checksum = request.GET['checksum']

    m = md5(checksum_str.encode("ascii"))
    checksum = m.hexdigest()

    # check if the payment was really successful
    if got_checksum != checksum:
        messages.error(request, "Invalid checksum. Your payment is invalid.")
        return render(request, 'payment/error.html')

    if result == "success":
        print("pid={}&ref={}&result={}&token={}".format(pid, ref, result, PAYMENT_SECRET))
        g = get_object_or_404(Game, pk=game_id)
        p = get_object_or_404(RegUser, pk=user_id)
        if PurchasedGame.objects.filter(player=p, game=g).exists():
            messages.error(request, g.name+" is already in your collection!")
            return render(request, 'payment/error.html')
        PurchasedGame.objects.create(game=g, player=p)
        GameSale.objects.create(game=g,
                                time_of_purchase=datetime.datetime.now(),
                                ref=ref,
                                pid=pid,
                                price_paid=g.price)
        return render(request, 'payment/success.html', {'game': g})

    elif result == "cancel":
        messages.info(request, "The purchase has been canceled as requested.")
        return redirect("purchase", gid=game_id)

    else:
        messages.error(request, "There was an error processing the payment. Please try again!")
        return render(request, 'payment/error.html')


@login_required(login_url='login')
def deletegame(request, gid):
    game = Game.objects.get(pk=gid)
    dev = user_from_req(request)

    if game.developer == dev:
        game.delete()
        return redirect("dashboard")

    return HttpResponseForbidden()


@login_required(login_url='login')
def editgame(request, gid):
    game = Game.objects.get(pk=gid)
    dev = user_from_req(request)

    if game.developer != dev:
        return HttpResponseForbidden()

    form = GameForm(request.POST or None, instance=game)

    if request.POST and form.is_valid():
        form.save()
        # Save was successful, so redirect to another page
        return redirect('dashboard')
    return render(request, 'editgame.html', {'form': form, 'game_id': gid})


def gameview(request, gid):
    game_view = get_object_or_404(Game, pk=gid)
    owned = False
    reviews = GameReview.objects.filter(game=gid)
    user = user_from_req(request)
    if user:
        if PurchasedGame.objects.filter(player=user, game=game_view).exists():
            owned = True
        if request.method == "POST":
            rev = request.POST.get('review')
            # only allow reviews with content and 1 review/user
            if rev and not GameReview.objects.filter(game=game_view, reviewer=user).exists():
                GameReview.objects.create(game=game_view, reviewer=user, review_text=rev)
    context = dict(game=game_view, reviews=reviews, owned=owned)
    return render(request, 'gameview.html', context)


def register(request):
    if request.method == 'POST':
        form = RegisterForm(data=request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            customuser = RegUser.objects.create(user=user)
            customuser.developer = form.cleaned_data.get('developer')
            customuser.save()
            current_site = get_current_site(request)
            subject = 'Activate Your MySite Account'
            message = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })
            user.email_user(subject, message)

            # Instead of sending out real email, account_activation_sent.html is used to simulate one
            return render(request, 'registration/account_activation_sent.html', {
                                   'user': user, 'domain':current_site.domain, 
                                   'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                                   'token': account_activation_token.make_token(user)})
            #return redirect('index')
    else:
        form = RegisterForm()
    return render(request, 'registration/register.html', {'form': form})


def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save();
        login(request, user)
        messages.success(request, "Account registered successfully!")
        return redirect('index')
    else:
        return HttpResponse('<h1>Page not found: invalid activation token</h1>')


def api_v1(request):
    return render(request, "api.html", {"app_url": request.path})


@login_required(login_url='login')
def api_v1_sales(request):
    user = user_from_req(request)

    callback = request.GET.get("callback")
    games = request.GET.get("games")
    from_date = request.GET.get("from")
    to_date = request.GET.get("to")
    if not games:
        # TODO: add link to api documentation or something
        return HttpResponse("ERROR: games parameter is required")
    games = map(lambda x: convert_or_none(int, x), games.split(","))
    games = list(filter(None.__ne__, games))

    response = {"games": []}
    game_queryset = Game.objects.filter(pk__in=games).filter(developer=user)
    for game in game_queryset:
        response["games"].append({
            "id": game.pk,
            "name": game.name,
            "sales": []
        })
        sales = GameSale.objects.filter(game=game)
        try:
            if from_date:
                sales = sales.filter(time_of_purchase__gte=from_date)
            if to_date:
                sales = sales.filter(time_of_purchase__lte=to_date)
        except ValidationError:
            return HttpResponse("ERROR: Invalid date format")
        for sale in sales:
            response["games"][-1]["sales"].append({
                "time_of_purchase": sale.time_of_purchase,
                "price_paid": sale.price_paid
            })

    if callback:
        return HttpResponse("{}({})".format(callback,
                                            json.dumps(response, default=str, indent=4)),
                                            content_type='application/javascript')
    return JsonResponse(response)


def api_v1_scores(request):
    callback = request.GET.get("callback")
    game = request.GET.get("game")
    min_score = convert_or_none(float, request.GET.get("min"))
    max_results = convert_or_none(int, request.GET.get("max_results"))
    if not max_results:
        max_results = 10
    if not game:
        # TODO: add link to api documentation or something
        return HttpResponse("ERROR: game parameter is required")

    try:
        game = int(game)
    except ValueError:
        return HttpResponse("ERROR: Parameter game should be game id")
    pgame_queryset = PurchasedGame.objects.filter(game=game).order_by("-high_score")
    response = {"high_scores": {}}
    for index, pgame in enumerate(pgame_queryset, start=1):
        if min_score and pgame.high_score < float(min_score):
            break
        response["high_scores"][index] = {
            "player": { "id": pgame.player.pk, "name": pgame.player.user.username },
            "score": pgame.high_score
        }
        if index >= max_results:
            break

    if callback:
        return HttpResponse("{}({})".format(callback,
                                            json.dumps(response, default=str, indent=4)),
                                            content_type='application/javascript')
    return JsonResponse(response)


def api_v1_games(request):
    callback = request.GET.get("callback")
    tags = request.GET.get("tags", None)
    if tags:
        tags = tags.split(",")
        game_queryset = Game.objects.filter(tags__name__in=tags)
    else:
        game_queryset = Game.objects.all()

    response = {"games": []}
    for game in game_queryset:
        response["games"].append({
            "id": game.id,
            "name": game.name,
            "price": game.price,
            "tags": list(map(lambda x: x.name, game.tags.all()))
        })

    if callback:
        return HttpResponse("{}({})".format(callback,
                                            json.dumps(response, default=str, indent=4)),
                                            content_type='application/javascript')
    return JsonResponse(response)
