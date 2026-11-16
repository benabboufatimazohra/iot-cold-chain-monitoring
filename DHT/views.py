#from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Dht11, Incident

#def test(request):
#   return HttpResponse("Iot Project")

def dashboard(request):
    # Rend juste la page; les données sont chargées via JS
    return render(request, "dashboard.html")

def latest_json(request):
    # Fournit la dernière mesure en JSON (sans passer par api.py)
    last = Dht11.objects.order_by('-dt').values('temp', 'hum', 'dt').first()
    if not last:
        return JsonResponse({"detail": "no data"}, status=404)
    return JsonResponse({
        "temperature": last["temp"],
        "humidity":    last["hum"],
        "timestamp":   last["dt"].isoformat()
    })
def graph_temp(request):
    return render(request,"graph_temp.html")
def graph_hum(request):
    return render(request,"graph_hum.html")

def incident_archive(request):
    incidents = Incident.objects.all().order_by('-start_at')
    return render(request, 'archive.html', {'incidents': incidents})

def incident_detail(request, pk):
    incident = get_object_or_404(Incident, id=pk)
    return render(request, 'incident_detail.html', {'incident': incident})
