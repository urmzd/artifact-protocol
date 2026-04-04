Create a Go gRPC service implementation for a notification service.

Include:
- Types: Notification, NotificationChannel (email, SMS, push), Template, DeliveryStatus
- Service struct implementing NotificationServiceServer with dependency injection
- Handlers: SendNotification, GetNotificationStatus, ListNotifications, UpdatePreferences, RegisterDevice
- Interceptors: logging, auth, rate limiting, panic recovery
- Helper functions for template rendering and channel-specific delivery
