def elements_available(request):
    """Контекстный процессор для проверки доступности приложения elements"""
    try:
        import elements
        return {'ELEMENTS_AVAILABLE': True}
    except ImportError:
        return {'ELEMENTS_AVAILABLE': False}