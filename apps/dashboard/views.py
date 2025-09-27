from django.shortcuts import render

def DashboardView(request):
    return render(request, 'dashboard/index.html')
