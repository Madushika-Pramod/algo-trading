import backtrader as bt
from statsmodels.tsa.arima.model import ARIMA


class ArimaStrategy(bt.Strategy):
    params = dict(arima_p=5, arima_d=1, arima_q=0)

    def __init__(self):
        # Keep track of the forecast
        self.model_fit = None
        self.forecast = None
        self.order_status = False
        self.order = None

    def next(self):
        # Get the most recent data
        recent_data = self.data.close.get(size=self.p.arima_p)

        # Update the ARIMA model with the most recent data
        # Now use the parameters from `params` dictionary
        model = ARIMA(recent_data, order=(self.p.arima_p, self.p.arima_d, self.p.arima_q))
        self.model_fit = model.fit(disp=0)

        # Forecast the next value
        self.forecast = self.model_fit.forecast(steps=1)[0]

        # Implement your strategy based on the forecast
        if not self.order_status and self.forecast > self.data.close[0]:
            # If the forecast is higher than the current price, then buy
            self.order = self.buy()
            self.order_status = True
        elif self.order_status and self.forecast < self.data.close[0]:
            # If the forecast is lower than the current price, then sell
            self.order = self.sell()
            self.order_status = False
