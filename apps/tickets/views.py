from rest_framework import generics, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter
from django.utils import timezone
from django.conf import settings

from .models import Ticket
from .serializers import (
    InitiateTicketSerializer,
    TicketSerializer,
    VerifyTicketSerializer,
)
from .payment import initialize_payment


@extend_schema(
    tags=['Tickets'],
    summary='List tickets for the organizer dashboard',
    description='Returns tickets with optional filtering by status and event.',
    parameters=[
        OpenApiParameter('status', str, description='Filter by ticket status'),
        OpenApiParameter('event', str, description='Filter by event slug'),
        OpenApiParameter('search', str, description='Search by ref, buyer name, or email'),
    ]
)
class TicketListView(generics.ListAPIView):
    serializer_class = TicketSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['reference', 'buyer_name', 'buyer_email', 'event__title']

    def get_queryset(self):
        queryset = Ticket.objects.select_related('event').order_by('-created_at')
        status = self.request.query_params.get('status')
        event = self.request.query_params.get('event')
        if status:
            queryset = queryset.filter(status=status)
        if event:
            queryset = queryset.filter(event__slug=event)
        return queryset


@extend_schema(
    tags=['Tickets'],
    summary='Initiate ticket purchase',
    description=(
        'Creates a pending ticket and returns a Flutterwave payment link. '
        'The user is redirected to Flutterwave to complete payment. '
        'On success, Flutterwave calls the webhook which confirms the ticket and triggers email delivery.'
    ),
    request=InitiateTicketSerializer,
    responses={
        201: OpenApiResponse(description='Payment link returned'),
        400: OpenApiResponse(description='Validation error'),
    }
)
class InitiateTicketView(APIView):

    def post(self, request):
        serializer = InitiateTicketSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        event = serializer.context['event']

        # Create pending ticket
        ticket = Ticket.objects.create(
            event=event,
            buyer_name=serializer.validated_data['buyer_name'],
            buyer_email=serializer.validated_data['buyer_email'],
            buyer_phone=serializer.validated_data.get('buyer_phone', ''),
            status=Ticket.Status.PENDING,
        )

        # Free event — confirm immediately, no payment needed
        if event.is_free:
            from .tasks import process_confirmed_ticket
            ticket.status = Ticket.Status.CONFIRMED
            ticket.amount_paid = 0
            ticket.save(update_fields=['status', 'amount_paid'])
            process_confirmed_ticket.delay(str(ticket.id))
            return Response({
                'message': 'Free ticket confirmed.',
                'ticket_reference': ticket.reference,
                'status': 'confirmed',
            }, status=status.HTTP_201_CREATED)

        # Paid event — get Flutterwave payment link
        frontend_url = settings.FRONTEND_URL.rstrip('/')
        redirect_url = f'{frontend_url}/event.html?slug={event.slug}'

        try:
            payment = initialize_payment(ticket, redirect_url=redirect_url)
        except Exception as e:
            ticket.delete()
            return Response({'error': str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Store tx_ref so we can match it in webhook
        ticket.flutterwave_tx_ref = payment['tx_ref']
        ticket.save(update_fields=['flutterwave_tx_ref'])

        return Response({
            'message': 'Proceed to payment.',
            'ticket_reference': ticket.reference,
            'payment_link': payment['payment_link'],
            'tx_ref': payment['tx_ref'],
        }, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Tickets'],
    summary='Verify ticket at the door (QR scan)',
    description=(
        'Takes a ticket reference (decoded from QR code) and marks it as scanned. '
        'Returns OK, Already Scanned, or Invalid. Call this from your scanner app.'
    ),
    request=VerifyTicketSerializer,
    responses={
        200: OpenApiResponse(description='Valid ticket — marked as scanned'),
        400: OpenApiResponse(description='Already scanned or invalid'),
    }
)
class VerifyTicketView(APIView):

    def post(self, request):
        serializer = VerifyTicketSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        reference = serializer.validated_data['reference'].strip().upper()

        try:
            ticket = Ticket.objects.select_related('event').get(reference=reference)
        except Ticket.DoesNotExist:
            return Response({
                'valid': False,
                'message': '❌ Invalid ticket — not found in system.',
            }, status=status.HTTP_400_BAD_REQUEST)

        if ticket.status == Ticket.Status.SCANNED:
            return Response({
                'valid': False,
                'message': f'⚠️ Already scanned at {ticket.scanned_at.strftime("%H:%M on %d %b")}.',
                'ticket': TicketSerializer(ticket).data,
            }, status=status.HTTP_400_BAD_REQUEST)

        if ticket.status != Ticket.Status.CONFIRMED:
            return Response({
                'valid': False,
                'message': f'❌ Ticket status is "{ticket.get_status_display()}" — not valid for entry.',
            }, status=status.HTTP_400_BAD_REQUEST)

        # All good — mark as scanned
        ticket.status = Ticket.Status.SCANNED
        ticket.scanned_at = timezone.now()
        ticket.save(update_fields=['status', 'scanned_at'])

        return Response({
            'valid': True,
            'message': f'✅ Valid! Welcome, {ticket.buyer_name}.',
            'ticket': TicketSerializer(ticket).data,
        }, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Tickets'],
    summary='Lookup ticket by reference',
    description='Returns ticket detail for a given reference code. Useful for support.'
)
class TicketDetailView(APIView):

    def get(self, request, reference):
        try:
            ticket = Ticket.objects.select_related('event').get(
                reference=reference.upper()
            )
        except Ticket.DoesNotExist:
            return Response({'error': 'Ticket not found.'}, status=status.HTTP_404_NOT_FOUND)

        return Response(TicketSerializer(ticket).data)
