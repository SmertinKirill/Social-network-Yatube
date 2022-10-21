import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    y = datetime.date.today().year
    return {
        'year': y
    }
