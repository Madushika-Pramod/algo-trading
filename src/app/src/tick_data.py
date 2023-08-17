from backtrader.feeds import GenericCSVData


class CustomTickData(GenericCSVData):
    lines = ('symbol', 'volume', 'last_price', 'lp_time', 'cumulative_change', 'cc_percentage')

    # Define the default columns for each line. Modify indices based on your CSV structure
    params = (
        ('datetime', 0),
        ('symbol', 1),
        ('volume', 2),
        ('last_price', 3),
        ('lp_time', 4),
        ('cumulative_change', 5),
        ('cc_percentage', 6),
        ('dtformat', ('%Y-%m-%d %H:%M:%S')),  # Date format
    )

