from users.models import UserTier
from django.shortcuts import redirect

class TierRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        user=request.user
        if not UserTier.objects.filter(user=user).exists():
            return redirect('user-tier-select')
        else:
            return super().dispatch(request, *args, **kwargs)