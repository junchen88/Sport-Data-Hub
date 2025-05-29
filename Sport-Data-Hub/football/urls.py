from django.urls import path # This is the path function
from . import views # This is the views file


# This is the list of our routes
urlpatterns = [
    path('returnScheduledMatches/<int:day>', views.returnScheduledMatches, name='returnScheduledMatches'),
]

