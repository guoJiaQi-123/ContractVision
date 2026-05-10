import datetime

import numpy as np
from dateutil.relativedelta import relativedelta
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract
from apps.users.permissions import IsAdmin
from core.response import error_response, success_response


class SalesPredictionView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def post(self, request):
        predict_months = int(request.data.get('predict_months', 6))
        history_months = int(request.data.get('history_months', 12))

        now = timezone.now()
        start_date = now - relativedelta(months=history_months)

        trends = (
            Contract.objects
            .filter(created_at__gte=start_date)
            .annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(count=Count('id'), amount=Sum('amount'))
            .order_by('month')
        )

        trend_list = list(trends)
        if len(trend_list) < 3:
            return error_response(message='历史数据不足，至少需要3个月的数据')

        amounts = [float(t['amount'] or 0) for t in trend_list]
        counts = [t['count'] for t in trend_list]
        months_labels = [t['month'].strftime('%Y-%m') for t in trend_list]

        try:
            from sklearn.linear_model import LinearRegression

            X = np.arange(len(amounts)).reshape(-1, 1)
            y_amount = np.array(amounts)
            y_count = np.array(counts)

            model_amount = LinearRegression()
            model_amount.fit(X, y_amount)

            model_count = LinearRegression()
            model_count.fit(X, y_count)

            future_X = np.arange(len(amounts), len(amounts) + predict_months).reshape(-1, 1)
            predicted_amounts = model_amount.predict(future_X)
            predicted_counts = model_count.predict(future_X)

            predicted_amounts = np.maximum(predicted_amounts, 0)
            predicted_counts = np.maximum(predicted_counts, 0).astype(int)

            last_month = trend_list[-1]['month']
            future_labels = []
            for i in range(1, predict_months + 1):
                next_month = last_month + relativedelta(months=i)
                future_labels.append(next_month.strftime('%Y-%m'))

            data = {
                'history': {
                    'months': months_labels,
                    'amounts': [str(round(a, 2)) for a in amounts],
                    'counts': counts,
                },
                'prediction': {
                    'months': future_labels,
                    'amounts': [str(round(float(a), 2)) for a in predicted_amounts],
                    'counts': [int(c) for c in predicted_counts],
                },
                'model_info': {
                    'type': 'LinearRegression',
                    'r2_amount': round(float(model_amount.score(X, y_amount)), 4),
                    'r2_count': round(float(model_count.score(X, y_count)), 4),
                },
            }
            return success_response(data=data)
        except ImportError:
            return error_response(message='未安装 scikit-learn，无法执行预测分析')
        except Exception as e:
            return error_response(message=f'预测分析失败: {str(e)}')


class AnomalyDetectionView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        contracts = Contract.objects.all()

        amounts = list(contracts.values_list('amount', flat=True))
        if len(amounts) < 5:
            return error_response(message='数据量不足，无法进行异常检测')

        float_amounts = [float(a) for a in amounts]
        mean_amount = np.mean(float_amounts)
        std_amount = np.std(float_amounts)

        threshold = mean_amount + 2 * std_amount
        lower_threshold = max(mean_amount - 2 * std_amount, 0)

        anomalies = contracts.filter(amount__gt=threshold) | contracts.filter(amount__lt=lower_threshold)

        from apps.contracts.serializers import ContractListSerializer
        serializer = ContractListSerializer(anomalies[:20], many=True)

        return success_response(data={
            'anomalies': serializer.data,
            'stats': {
                'mean_amount': str(round(mean_amount, 2)),
                'std_amount': str(round(std_amount, 2)),
                'upper_threshold': str(round(threshold, 2)),
                'lower_threshold': str(round(lower_threshold, 2)),
                'anomaly_count': anomalies.count(),
            },
        })


class CustomerValueView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        clients = (
            Contract.objects
            .values('client_name')
            .annotate(
                contract_count=Count('id'),
                total_amount=Sum('amount'),
            )
            .order_by('-total_amount')
        )

        client_list = list(clients)
        if not client_list:
            return success_response(data={'clients': [], 'segments': {}})

        amounts = [float(c['total_amount'] or 0) for c in client_list]
        max_amount = max(amounts) if amounts else 1

        high_value = []
        medium_value = []
        low_value = []

        for client in client_list:
            amount = float(client['total_amount'] or 0)
            score = (amount / max_amount * 60) + (min(client['contract_count'], 10) / 10 * 40)

            client_data = {
                'client_name': client['client_name'],
                'contract_count': client['contract_count'],
                'total_amount': str(client['total_amount'] or 0),
                'value_score': round(score, 1),
            }

            if score >= 70:
                client_data['level'] = '高价值'
                high_value.append(client_data)
            elif score >= 40:
                client_data['level'] = '中价值'
                medium_value.append(client_data)
            else:
                client_data['level'] = '低价值'
                low_value.append(client_data)

        return success_response(data={
            'clients': high_value + medium_value + low_value,
            'segments': {
                'high': len(high_value),
                'medium': len(medium_value),
                'low': len(low_value),
            },
        })
