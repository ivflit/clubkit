"""
Signal handlers that trigger email notifications on Membership lifecycle events.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from memberships.models import Membership


@receiver(post_save, sender=Membership)
def on_membership_saved(sender, instance, update_fields, **kwargs):
    """Fire lapsed notification when a Membership is transitioned to 'lapsed'."""
    if update_fields is None:
        return
    if "status" not in update_fields:
        return
    if instance.status != "lapsed":
        return

    from notifications.services import send_membership_lapsed_email

    send_membership_lapsed_email(instance)
