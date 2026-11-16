from .models import Dht11, Incident
from .serializers import DHT11serialize, IncidentSerializer
from rest_framework.decorators import api_view
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import rest_framework

MIN_OK = 2
MAX_OK = 8


def send_temperature_alert(temp, when):
    """E-mail the operators when a reading leaves the safe 2-8 °C range."""
    if not settings.ALERT_EMAIL_RECIPIENTS:
        return
    kind = "basse" if temp < MIN_OK else "haute"
    try:
        send_mail(
            subject=f"⚠️ Alerte température {kind} : {temp:.1f} °C",
            message=(
                f"La température a atteint {temp:.1f} °C à {when}, "
                f"hors de la plage autorisée ({MIN_OK}-{MAX_OK} °C). Un incident a été ouvert."
            ),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=settings.ALERT_EMAIL_RECIPIENTS,
            fail_silently=True,
        )
    except Exception:
        pass


@api_view(['GET'])
def Dlist(request):
    all_data = Dht11.objects.all()
    data = DHT11serialize(all_data, many=True).data
    return Response({'data': data})

class Dhtviews(generics.CreateAPIView):
    queryset = Dht11.objects.all()
    serializer_class = DHT11serialize

    def perform_create(self, serializer):
        instance = serializer.save()

        # Incident management logic
        t = instance.temp
        if t is None:
            return

        is_incident = (t < MIN_OK or t > MAX_OK)

        # récupérer l'incident ouvert (s'il existe)
        incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()

        if is_incident:
            # si pas d'incident ouvert -> en créer un et alerter par e-mail (une seule fois par incident)
            if incident is None:
                incident = Incident.objects.create(is_open=True, counter=0, max_temp=t)
                send_temperature_alert(t, instance.dt)

            incident.counter += 1
            if t > incident.max_temp:
                incident.max_temp = t
            incident.save()

        else:
            # température OK -> si incident ouvert, on le ferme
            if incident is not None:
                incident.is_open = False
                incident.end_at = timezone.now()
                incident.save()


# ---- API incident: état courant ----
class IncidentStatus(APIView):
    def get(self, request):
        incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
        if not incident:
            return Response({"is_open": False, "counter": 0})
        return Response(IncidentSerializer(incident).data)


# ---- API incident: valider ACK + commentaire (op1/op2/op3) ----
class IncidentUpdateOperator(APIView):
    def post(self, request):
        """
        body:
        {
          "op": 1,
          "ack": true,
          "comment": "..."
        }
        """
        op = int(request.data.get("op", 1))
        ack = bool(request.data.get("ack", False))
        comment = request.data.get("comment", "")

        incident = Incident.objects.filter(is_open=True).order_by("-start_at").first()
        if not incident:
            return Response({"error": "no open incident"}, status=400)

        now = timezone.now()

        if op == 1:
            incident.op1_ack = ack
            incident.op1_comment = comment
            incident.op1_saved_at = now
        elif op == 2:
            incident.op2_ack = ack
            incident.op2_comment = comment
            incident.op2_saved_at = now
        else:
            incident.op3_ack = ack
            incident.op3_comment = comment
            incident.op3_saved_at = now

        incident.save()
        return Response(IncidentSerializer(incident).data)
