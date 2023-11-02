from app.src import constants
from app.src.cli_v2 import run_single, run_parallel, test_config_process
import argparse

from broker.src.alpaca_data import AlpacaHistoricalData

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', choices=['algo', 'tune', 'data', 'test'])
    parser.add_argument('--values', type=float, nargs=5)
    parser.add_argument('--count', type=int, nargs=2)
    parser.add_argument('--paths', type=str, nargs=3)

    args = parser.parse_args()

    if args.run == 'algo':
        import logger_config

        run_single(buy_profit_threshold=args.values[0], slow_ma_period=int(args.values[1]),
                   high_low_period=int(args.values[2]), high_low_tolerance=args.values[3],
                   sell_profit_threshold=args.values[4])
    elif args.run == 'tune':
        run_parallel(start_count=args.count[0], increment=args.count[1], processing_units=7)
    elif args.run == 'data':
        import logger_config
        import os

        os.environ['API_KEY'] = 'PK2TQTQ9K2BE9UFZ3GEF'
        os.environ['SECRET_KEY'] = 'pJAGlSqs8QsgPyCknLLE2qdWcxvgZdAfCDtkW84H'

        AlpacaHistoricalData(constants.symbol, constants.period_in_days, constants.csv_file_path).save_to_csv()
    elif args.run == 'test':
        configurations = dict(input_file_path=args.paths[0], out_put_file_path=args.paths[1],
                              data_file_path=args.paths[2])

        run_parallel(config_process=test_config_process, configurations=configurations, start_count=args.count[0],
                     increment=args.count[1], processing_units=2)

'sssss'
# buy_profit_threshold, slow_ma_period, high_low_period, high_low_tolerance, sell_profit_threshold
# pdm run python src/app/src/run.py --run algo --values 1 15 21 0.5 3

# pdm run python src/app/src/run.py --run tune --count 1000 4
# pdm run tune --count 1000 -2000
