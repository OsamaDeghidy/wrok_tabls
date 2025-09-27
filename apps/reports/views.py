from django.shortcuts import render
from django.http import HttpResponse

def ReportListView(request):
    return render(request, 'reports/list.html')

def ReportCreateView(request):
    return HttpResponse("Report Create")

def ReportDetailView(request, pk):
    return HttpResponse(f"Report Detail: {pk}")

def ReportDownloadView(request, pk):
    return HttpResponse(f"Report Download: {pk}")

def ReportDeleteView(request, pk):
    return HttpResponse(f"Report Delete: {pk}")