import re

from django.core.exceptions import ValidationError


def validate_phone(value):
    pattern = r'^1[3-9]\d{9}$'
    if not re.match(pattern, value):
        raise ValidationError('手机号格式不正确')


def validate_contract_no(value):
    pattern = r'^[A-Z]{2,4}-\d{4}-\d{4,8}$'
    if not re.match(pattern, value):
        raise ValidationError('合同编号格式不正确，应为 XX-YYYY-NNNNN 格式')


def validate_positive_amount(value):
    if value <= 0:
        raise ValidationError('金额必须大于零')


def validate_password_strength(value):
    if len(value) < 8:
        raise ValidationError('密码长度不能少于8位')
    if not re.search(r'[A-Z]', value):
        raise ValidationError('密码必须包含至少一个大写字母')
    if not re.search(r'[a-z]', value):
        raise ValidationError('密码必须包含至少一个小写字母')
    if not re.search(r'\d', value):
        raise ValidationError('密码必须包含至少一个数字')
