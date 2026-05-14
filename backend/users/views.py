from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils import timezone
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.serializers import (
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RoleUpdateSerializer,
    UserDetailSerializer,
    UserRegistrationSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new User within the current Tenant's schema."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserDetailSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class MeView(generics.RetrieveAPIView):
    """Return the currently authenticated User."""

    serializer_class = UserDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class RoleUpdateView(APIView):
    """Allow Admins to change another User's role."""

    permission_classes = [IsAuthenticated]

    def patch(self, request, user_id):
        if not request.user.is_tenant_admin:
            return Response(
                {"detail": "Only Admins can change roles."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            target_user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"detail": "User not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = RoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        target_user.role = serializer.validated_data["role"]
        target_user.save(update_fields=["role"])
        return Response(UserDetailSerializer(target_user).data)


class PasswordResetRequestView(APIView):
    """Request a password reset. Returns token+uid directly (email in production)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            # Don't reveal whether the email exists
            return Response(
                {"detail": "If an account with that email exists, a reset link has been sent."},
                status=status.HTTP_200_OK,
            )

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # In production, send email with reset link. For now, return directly.
        return Response(
            {
                "detail": "If an account with that email exists, a reset link has been sent.",
                "uid": uid,
                "token": token,
            },
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    """Return the authenticated User's dashboard data: active memberships and upcoming events."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        from memberships.models import Membership
        from events.models import EventRegistration

        active_memberships = (
            Membership.objects.filter(owner=request.user, status="active")
            .select_related("membership_type")
            .order_by("end_date")
        )

        upcoming_registrations = (
            EventRegistration.objects.filter(
                user=request.user,
                event__status="upcoming",
                event__date_time__gte=timezone.now(),
            )
            .select_related("event")
            .order_by("event__date_time")
        )

        memberships_data = [
            {
                "id": m.id,
                "membership_type": m.membership_type.id,
                "membership_type_name": m.membership_type.name,
                "status": m.status,
                "start_date": m.start_date.isoformat(),
                "end_date": m.end_date.isoformat() if m.end_date else None,
            }
            for m in active_memberships
        ]

        events_data = [
            {
                "id": reg.event.id,
                "title": reg.event.title,
                "date_time": reg.event.date_time.isoformat(),
                "location": reg.event.location,
            }
            for reg in upcoming_registrations
        ]

        return Response(
            {
                "active_memberships": memberships_data,
                "upcoming_events": events_data,
            }
        )


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token and new password."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data["uid"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response(
                {"detail": "Invalid reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, serializer.validated_data["token"]):
            return Response(
                {"detail": "Invalid or expired reset link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response(
            {"detail": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )
