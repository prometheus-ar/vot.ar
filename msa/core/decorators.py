from msa.helpers import reset_locales, cambiar_locale, locale_actual


def forzar_idioma(locale):
    def wrap(f):
        def wrapped_f(*args, **kwargs):
            locale = locale_actual()
            reset_locales()

            response = f(*args, **kwargs)
            cambiar_locale(locale)
            return response

        return wrapped_f
    return wrap
