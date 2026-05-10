import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "contract_vision.settings")
django.setup()
from django.test import RequestFactory
from apps.analytics.views import DashboardStatsView
factory = RequestFactory()
request = factory.get('/')
view = DashboardStatsView.as_view()
response = view(request)
print(response.data)
