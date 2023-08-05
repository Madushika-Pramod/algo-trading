# Alpaca-Backtrader Algorithmic Trading Bot

Welcome to our algorithmic trading bot, designed to harness the power of Alpaca's API and backtrader in Python. This trading bot seamlessly supports both backtesting and live trading of custom strategies.

## 🎯 Core Capabilities

- **Efficient Backtesting:** Rapidly test your strategies against historical market data for quick evaluations.
- **Real-time Live Trading:** Harness Alpaca's commission-free API to implement automated trading in real time.
- **Strategies Customization:** The bot allows for an intuitive implementation of strategies using Python, tailoring the bot to your trading approach.

We strongly advise understanding the potential financial risks associated with algorithmic trading. Thorough backtesting is recommended before proceeding to live trading.

## 🔧 System Requirements

- Python 3.9
- Pdm ([Installation Guide](https://pdm.fming.dev/latest/))

## 💻 Installation & Configuration Steps

1. Clone the repository:
    ```
    git clone https://github.com/Madushika-Pramod/Alpaca-Backtrader.git
    ```

2. Navigate to the cloned repository directory:
    ```
    cd Alpaca-Backtrader
    ```

3. Install necessary requirements:
    ```
    brew install pdm
    pdm install
    ```
   Use `pdm add <package name>` to add new packages.

## 🔐 Alpaca API Keys Setup

Input your Alpaca API_KEY and SECRET_KEY in your environment variables. If you require assistance in acquiring these keys, please refer to the [Alpaca API documentation](https://alpaca.markets/docs/api-documentation/).

## ⚙️ Customizing Your Bot

The bot's operational parameters can be adjusted by modifying the constant values in the `Constant.py` file.

## 🚀 Execution

To initiate the trading bot, execute `cli.py`.

## 🤝 How to Contribute

1. Fork the repository.
2. Create a new branch: `git checkout -b <branch_name>`.
3. Commit your changes: `git commit -m '<commit_message>'`
4. Push to the original branch: `git push origin <project_name>/<location>`
5. Create a pull request.

## 📬 Get in Touch

If you encounter any issues or have queries, feel free to contact us via email at `madushika4@gmail.com`.

## 📜 Licensing

This project operates under the [MIT License](https://opensource.org/licenses/MIT).
