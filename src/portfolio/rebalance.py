import math


def simulate(total_value, current_duration, sale_value, sale_duration, target_duration, purchase_duration):
    values = [total_value,current_duration,sale_value,sale_duration,target_duration,purchase_duration]
    if not all(math.isfinite(v) for v in values) or total_value <= 0 or not 0 < sale_value <= total_value:
        raise ValueError('Importes inválidos: la venta debe ser positiva y no superar la cartera')
    if min(current_duration,sale_duration,target_duration,purchase_duration) < 0:
        raise ValueError('Las durations ingresadas deben ser no negativas')
    weight = sale_value / total_value
    required = sale_duration + (target_duration - current_duration) / weight
    after = current_duration + weight * (purchase_duration - sale_duration)
    return {'Duration actual': current_duration, 'Duration objetivo': target_duration,
            'Duration necesaria de compra': required, 'Duration simulada': after,
            'Diferencia con objetivo': after-target_duration, 'Importe reemplazado': sale_value,
            'Peso reemplazado': weight}
