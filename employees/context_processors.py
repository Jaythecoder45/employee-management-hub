from .models import Notification

def notifications_processor(request):
    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')[:8]
        unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return {
            'unread_notifications': unread_notifications,
            'unread_notifications_count': unread_count,
        }
    return {
        'unread_notifications': [],
        'unread_notifications_count': 0,
    }
