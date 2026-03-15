import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'worktable_system.settings')
django.setup()

from django.contrib.auth.models import User
from apps.notifications.models import Notification

def debug_notifications():
    users = User.objects.all()
    for user in users:
        all_count = Notification.objects.filter(recipient=user).count()
        unread_count = Notification.objects.filter(recipient=user, is_read=False).count()
        if all_count > 0:
            print(f"User: {user.username} | Total: {all_count} | Unread: {unread_count}")
            for n in Notification.objects.filter(recipient=user)[:3]:
                print(f"  - [{n.is_read}] {n.title}: {n.message[:30]}...")

if __name__ == "__main__":
    debug_notifications()
