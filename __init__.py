# __init__.py

def classFactory(iface):
    """Load ErrorInterceptorPlugin class from file ErrorInterceptorPlugin."""
    from .ErrorInterceptorPlugin import ErrorInterceptorPlugin
    return ErrorInterceptorPlugin(iface)

