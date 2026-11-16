from django.db import models

class Dht11(models.Model):
    temp = models.FloatField(null=True)
    hum = models.FloatField(null=True)
    dt = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ["-dt"]

    def __str__(self):
        return f"{self.dt} -> T={self.temp}°C, H={self.hum}%"

class Incident(models.Model):
    start_at = models.DateTimeField(auto_now_add=True)         # début incident
    end_at   = models.DateTimeField(null=True, blank=True)     # fin incident
    is_open  = models.BooleanField(default=True)

    counter  = models.IntegerField(default=0)                  # nb mesures hors plage
    max_temp = models.FloatField(default=0)

    # opérateurs
    op1_ack = models.BooleanField(default=False)
    op2_ack = models.BooleanField(default=False)
    op3_ack = models.BooleanField(default=False)

    op1_comment = models.TextField(blank=True)
    op2_comment = models.TextField(blank=True)
    op3_comment = models.TextField(blank=True)

    op1_saved_at = models.DateTimeField(null=True, blank=True)
    op2_saved_at = models.DateTimeField(null=True, blank=True)
    op3_saved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Incident #{self.id} ({'OPEN' if self.is_open else 'CLOSED'}) counter={self.counter}"
