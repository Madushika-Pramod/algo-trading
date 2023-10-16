from app.src.cli_v2 import run_single, run_parallel
import argparse

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument('--run', choices=['algo', 'tune'])
    parser.add_argument('--values', type=float, nargs=5)
    parser.add_argument('--count', type=int, nargs=1)

    args = parser.parse_args()

    if args.run == 'algo':
        run_single(buy_profit_threshold=args.values[0], slow_ma_period=int(args.values[1]), high_low_period=int(args.values[2]), high_low_tolerance=args.values[3],
               sell_profit_threshold=args.values[4])
    elif args.run == 'tune':
        run_parallel(pre_count=args.count[0])

# buy_profit_threshold, slow_ma_period, high_low_period, high_low_tolerance, sell_profit_threshold
# pdm run python src/app/src/run.py --run algo --values 1 15 21 0.5 3

# pdm run python src/app/src/run.py --run tune --count 1000