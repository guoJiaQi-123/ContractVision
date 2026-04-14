from django.db.models import Avg, Count, Sum
from django.db.models.functions import TruncMonth
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.contracts.models import Contract
from apps.users.permissions import IsOperator
from core.response import error_response, success_response
from utils.export import export_to_excel, export_to_pdf


class ReportGenerateView(APIView):
    permission_classes = [IsAuthenticated, IsOperator]

    def post(self, request):
        report_type = request.data.get('report_type', 'monthly_summary')
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')

        queryset = Contract.objects.all()
        if start_date:
            queryset = queryset.filter(sign_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(sign_date__lte=end_date)

        if report_type == 'monthly_summary':
            data = self._monthly_summary(queryset)
        elif report_type == 'client_analysis':
            data = self._client_analysis(queryset)
        elif report_type == 'product_analysis':
            data = self._product_analysis(queryset)
        elif report_type == 'region_analysis':
            data = self._region_analysis(queryset)
        elif report_type == 'salesperson_analysis':
            data = self._salesperson_analysis(queryset)
        else:
            return error_response(message='不支持的报表类型')

        return success_response(data=data)

    def _monthly_summary(self, queryset):
        results = (
            queryset
            .annotate(month=TruncMonth('sign_date'))
            .values('month')
            .annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
                avg_amount=Avg('amount'),
            )
            .order_by('month')
        )
        return {
            'title': '月度销售合同汇总表',
            'columns': ['月份', '合同数量', '合同总金额', '平均金额'],
            'rows': [
                {
                    'month': item['month'].strftime('%Y-%m') if item['month'] else '',
                    'count': item['count'],
                    'total_amount': str(item['total_amount'] or 0),
                    'avg_amount': str(round(item['avg_amount'] or 0, 2)),
                }
                for item in results
            ],
        }

    def _client_analysis(self, queryset):
        results = (
            queryset
            .values('client_name')
            .annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
                avg_amount=Avg('amount'),
            )
            .order_by('-total_amount')
        )
        return {
            'title': '客户业绩贡献表',
            'columns': ['客户名称', '合同数量', '合同总金额', '平均金额'],
            'rows': [
                {
                    'client_name': item['client_name'],
                    'count': item['count'],
                    'total_amount': str(item['total_amount'] or 0),
                    'avg_amount': str(round(item['avg_amount'] or 0, 2)),
                }
                for item in results
            ],
        }

    def _product_analysis(self, queryset):
        results = (
            queryset
            .exclude(product_type='')
            .values('product_type')
            .annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
            )
            .order_by('-total_amount')
        )
        total_amount = sum(float(r['total_amount'] or 0) for r in results)
        return {
            'title': '产品销售分析表',
            'columns': ['产品类型', '合同数量', '合同总金额', '占比'],
            'rows': [
                {
                    'product_type': item['product_type'],
                    'count': item['count'],
                    'total_amount': str(item['total_amount'] or 0),
                    'percentage': f"{(float(item['total_amount'] or 0) / total_amount * 100):.1f}%" if total_amount > 0 else '0%',
                }
                for item in results
            ],
        }

    def _region_analysis(self, queryset):
        results = (
            queryset
            .exclude(region='')
            .values('region')
            .annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
            )
            .order_by('-total_amount')
        )
        return {
            'title': '区域业绩统计表',
            'columns': ['区域', '合同数量', '合同总金额'],
            'rows': [
                {
                    'region': item['region'],
                    'count': item['count'],
                    'total_amount': str(item['total_amount'] or 0),
                }
                for item in results
            ],
        }

    def _salesperson_analysis(self, queryset):
        results = (
            queryset
            .exclude(salesperson='')
            .values('salesperson')
            .annotate(
                count=Count('id'),
                total_amount=Sum('amount'),
                avg_amount=Avg('amount'),
            )
            .order_by('-total_amount')
        )
        return {
            'title': '销售人员业绩分析表',
            'columns': ['销售人员', '合同数量', '合同总金额', '平均金额'],
            'rows': [
                {
                    'salesperson': item['salesperson'],
                    'count': item['count'],
                    'total_amount': str(item['total_amount'] or 0),
                    'avg_amount': str(round(item['avg_amount'] or 0, 2)),
                }
                for item in results
            ],
        }


class ReportExportView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        export_format = request.data.get('format', 'excel')
        report_data = request.data.get('report_data', {})

        if not report_data or not report_data.get('rows'):
            return error_response(message='无数据可导出')

        title = report_data.get('title', '报表')
        col_names = report_data.get('columns', [])
        rows = report_data.get('rows', [])

        if not rows:
            return error_response(message='报表数据为空')

        keys = list(rows[0].keys()) if rows else []
        columns = [
            {'key': k, 'label': col_names[i] if i < len(col_names) else k, 'width': 20, 'pdf_width': 80}
            for i, k in enumerate(keys)
        ]

        if export_format == 'pdf':
            return export_to_pdf(rows, columns, title=title, filename=f'{title}.pdf')
        else:
            return export_to_excel(rows, columns, filename=f'{title}.xlsx')
