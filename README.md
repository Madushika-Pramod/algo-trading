# Alpaca-Backtrader Trading Bot

This repository hosts a Python-based trading bot developed to leverage Alpaca's API and backtrader. The bot supports both backtesting and live trading of algorithmic strategies.

## 🎯 Key Features

- **Backtesting:** Facilitates quick testing against historical market data.
- **Live Trading:** Enables real-time automated trading through Alpaca's commission-free API.
- **Customizable Strategies:** Offers an intuitive implementation of strategies via Python.

Please be informed of the potential financial risks associated with algorithmic trading. It is strongly advised to conduct comprehensive backtesting before moving on to live deployment.

## 🔧 Prerequisites

- Python 3.9
- Pdm ([Installation Guide](https://pdm.fming.dev/latest/))

## 💻 Installation and Setup

1. Clone the repository:
    ```
    git clone https://github.com/Madushika-Pramod/Alpaca-Backtrader.git
    ```

2. Navigate to the cloned repository directory:
    ```
    cd Alpaca-Backtrader
    ```

3. Install requirements:
    ```
    brew install pdm
    pdm install  
    ``
   pdm add <package name>
## 🔐 API Configuration

Add your Alpaca API_KEY and SECRET_KEY to your environment variables. If you need assistance in obtaining these values, refer to the [Alpaca API documentation](https://alpaca.markets/docs/api-documentation/).

## ⚙️ Constant Configuration

You can customize the bot's operation by modifying the constant values in the `Constant.py` file.

## 🚀 Usage

To execute the trading bot, run `main.py`.

## 🤝 Contribution

1. Fork the repository.
2. Create a new branch: `git checkout -b <branch_name>`.
3. Commit your changes: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create a pull request.

## 📬 Contact

For any queries or issues, feel free to reach out via email at `madushika4@gmail.com`.

## 📜 License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
