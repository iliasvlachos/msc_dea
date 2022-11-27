from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm
from django.contrib.auth.decorators import login_required
from .models import Tier, UserTier
from django.urls import reverse
from django.http import HttpResponseRedirect


# Create your views here.
def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')
            return redirect('dea-index')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


@login_required()
def account(request):
    user = request.user
    user_tier = UserTier.objects.get(user=user)
    context = {'user_tier': user_tier}
    return render(request, 'users/account.html', context)


def tier_select(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            tiers = Tier.objects.all()
            for tier in tiers:
                print("in tiers for")
                title = request.POST.get("selected_tier")
                print(title)
                # selected_tier = Tier.objects.get(title=request.POST.get(tier.title))
                if tier.title == title:
                    print("found title " + str(title))
                    selected_tier = get_object_or_404(Tier, title=title)
                    if UserTier.objects.filter(user=request.user).exists():
                        user_tier = UserTier.objects.get(user=request.user)
                        user_tier.tier = selected_tier
                        user_tier.save()
                    else:
                        UserTier.objects.create(user=request.user, tier=selected_tier)
            return HttpResponseRedirect(reverse('projects-list'))
        else:
            return HttpResponseRedirect(reverse('user-login'))
    else:
        tiers = Tier.objects.all()
        context = {'tiers': tiers}
        return render(request, 'users/tiers.html', context)
