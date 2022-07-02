import matplotlib.pyplot as plt
import random

"""
SIMPLE MOVING AVERAGE 

:param smoothing_settings: A dictionary of all the inputs for the SMA equation

:return The simple moving average of the most recent point
"""


def SMA(smoothing_settings):
    # The most recent k points
    prev_k_points = smoothing_settings['prev_k_points']
    # The window of points to be used
    k = smoothing_settings['sma_k']

    if k > len(prev_k_points):
        return prev_k_points[-1]
    elif k == len(prev_k_points):
        # returns the average of the most recent data points within the given window
        return sum(prev_k_points) / k
    else:
        raise Exception("More than k points have been given for smoothing")


"""
EXPONENTIAL MOVING AVERAGE

:param data - most recent data point
:param smoothing_settings: A dictionary of all the inputs for the SMA equation

:return the exponential moving average at the most recent point
"""


def EMA(data, settings):
    window = settings['ema_k']
    smoothing = settings['ema_s']
    EMA_prev = settings['previous_ema']

    alpha = smoothing / (1 + window)

    if (EMA_prev):
        return data * alpha + EMA_prev * (1 - alpha)
    else:
        return data


if __name__ == '__main__':

    settings = {'sma_active': True, 'sma_k': 10, 'prev_k_points': [], 'ema_active': True, 'ema_k': 10,
                'ema_s': 1, 'previous_ema': None}

    # Random data is generated
    rand_data = [random.randrange(30, 50, 2) for i in range(100)]
    data = []

    for i in rand_data:
        settings['prev_k_points'].append(i)

        if settings['sma_k'] > len(settings['prev_k_points']):
            data.append(SMA(settings))
        else:
            data.append(SMA(settings))
            settings['prev_k_points'].pop(0)

    # sma data is taken from the waveform
    settings['prev_k_points'] = []
    SMA_data = []
    for i in data:
        settings['prev_k_points'].append(i)

        if settings['sma_k'] > len(settings['prev_k_points']):
            SMA_data.append(SMA(settings))
        else:
            SMA_data.append(SMA(settings))
            settings['prev_k_points'].pop(0)

    # ema data is taken from the waveform
    EMA_data = []
    for i in data:
        EMA_data.append(EMA(i, settings))
        settings['previous_ema'] = EMA_data[-1]

    plt.plot(data, "r")
    plt.plot(SMA_data, "b")
    plt.plot(EMA_data, "g")
    plt.show()
