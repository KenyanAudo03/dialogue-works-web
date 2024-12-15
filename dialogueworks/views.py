from django.shortcuts import render

def homepage(request):
    return render(request, 'dialogueswork/homepage.html')
def contact(request):
    return render(request, 'dialogueswork/contact.html')
