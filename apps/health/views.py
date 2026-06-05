from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.db import connection
from django.utils import timezone
import django


@extend_schema(
    tags=['Health'],
    summary='Health check',
    description=(
        'Returns system status. Checks DB connectivity. '
        'Point UptimeRobot at this endpoint — expect HTTP 200 with `"status": "ok"`.'
    ),
    responses={200: None}
)
class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # Check DB
        db_ok = False
        try:
            connection.ensure_connection()
            db_ok = True
        except Exception:
            pass

        payload = {
            'status': 'ok' if db_ok else 'degraded',
            'timestamp': timezone.now().isoformat(),
            'django_version': django.VERSION,
            'database': 'connected' if db_ok else 'error',
        }

        status_code = 200 if db_ok else 503
        return Response(payload, status=status_code)
