from rest_framework import serializers

from .models import AnalyticsSnapshot


class AnalyticsSnapshotSerializer(serializers.ModelSerializer):

    class Meta:
        model = AnalyticsSnapshot
        fields = '__all__'


class DashboardStatsSerializer(serializers.Serializer):
    total_contracts = serializers.IntegerField()
    total_amount = serializers.DecimalField(max_digits=18, decimal_places=2)
    active_contracts = serializers.IntegerField()
    completed_contracts = serializers.IntegerField()
    this_month_new = serializers.IntegerField()
    this_month_amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class TrendDataSerializer(serializers.Serializer):
    date = serializers.DateField()
    count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class RegionDistributionSerializer(serializers.Serializer):
    region = serializers.CharField()
    count = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=2)


class StatusDistributionSerializer(serializers.Serializer):
    status = serializers.CharField()
    count = serializers.IntegerField()
