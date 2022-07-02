import matplotlib.pyplot as plt
import random
"""
SIMPLE MOVING AVERAGE 

:param Data: the list of data points
:param Window: The number of most recent data points used to calculate the moving average

:return The simple moving average of the most recent point
"""
def SMA(data, window):
    # returns the average of the most recent data points within the given window
    return sum(data[-window:]) / window


"""
EXPONENTIAL MOVING AVERAGE

:param data - list of data points
:param window - the number of most recent data points used to calculate the moving average
:param smoothing
:param EMA_prev - previous exponential moving average

:return the exponential moving average at the most recent point
"""
def EMA(data, window, smoothing, EMA_prev):
    alpha = smoothing / (1 + window)

    return data[-1] * alpha + EMA_prev * (1 - alpha)

if __name__ == '__main__':
    data = [random.randrange(30, 50, 2) for i in range(100)]
    data = [SMA(data[:i], 5) if i >= 5 else data[i] for i in range(len(data))]

    k = 10
    s = 1

    SMA_data = [SMA(data[:i], k) if i >= k else data[i] for i in range(len(data))]

    EMA_data = [0] * len(data)
    for i in range(len(data)):
        if i <= k:
            EMA_data[i] = data[i]

        else:
            EMA_data[i] = EMA(data[:i], k, s, EMA_data[i-1])

    plt.plot(data, "r")
    plt.plot(SMA_data, "b")
    plt.plot(EMA_data, "g")
    plt.show()

