import MetaTrader5 as mt5
import time
import pandas as pd
import numpy as np
from datetime import datetime
import logging

# Configure logging
# # B # A # C # K # U # P # C # O # D # E # #
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Watermark (author information) DO NOT DELETE pls pls pls
__author__ = "Prince Mercado"
__version__ = "08.11"
__copyright__ = "(c) 2024 Prince Mercado"

HASH_1 = "01a1819e56908f55d89c5452055e7bc2949ec244d7e2f8dfebb1db8e0aa197cf"
HASH_2 = "e6428d2fc9c4e9b674615b78f497f21181d39c3a7f2eef8ee764b09531248557"
HASH_3 = "380b1443e72d7387d742d66fa935ad192c6f9d8ec6900e01b46fc16f56cb11b7"

symbol = "XAUUSD.s"

# Check session time
def check_time_and_display_message():
    while True:
        current_time = datetime.now().time()

        start_time = current_time.replace(hour=1, minute=0, second=0, microsecond=0)
        end_time = current_time.replace(hour=23, minute=0, second=0, microsecond=0)

        if start_time <= current_time <= end_time:
            logging.info("Session Activated!")
            check_ma_and_execute_logic()
            break
        else:
            logging.info("It's not between the specified session time.")
            time.sleep(1)

# Get bid and ask prices
def get_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"Failed to retrieve tick data for symbol {symbol}!")
        return None, None
    return tick.bid, tick.ask

# Close positions
def close_positions(position, symbol):
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        logging.error(f"Failed to retrieve tick data for symbol {position.symbol}!")
        return

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position.ticket,
        "symbol": symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_BUY if position.type == 1 else mt5.ORDER_TYPE_SELL,
        "price": tick.ask if position.type == 1 else tick.bid,
        "deviation": 20,
        "magic": 6102024,
        "comment": "Minero Gold Close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Failed to close position {position.ticket}. Error: {result.comment}")

# Calculate Moving Averages
def calculate_ma(data, period):
    return data['close'].rolling(window=period).mean()

# Check MA crossover and execute main logic
def check_ma_and_execute_logic():
    while True:
        # Fetch historical data
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
        if rates is None:
            logging.error(f"Failed to retrieve rates for symbol {symbol}!")
            time.sleep(1)
            continue

        data = pd.DataFrame(rates)
        ma_5 = calculate_ma(data, 5)
        ma_8 = calculate_ma(data, 8)

        latest_ma_5 = ma_5.iloc[-1]
        latest_ma_8 = ma_8.iloc[-1]
        previous_ma_5 = ma_5.iloc[-2]
        previous_ma_8 = ma_8.iloc[-2]

        logging.info(f"Latest MA 5: {latest_ma_5}, Latest MA 8: {latest_ma_8}")

        if (previous_ma_5 < previous_ma_8 and latest_ma_5 > latest_ma_8) or (previous_ma_5 > previous_ma_8 and latest_ma_5 < latest_ma_8):
            logging.info("MA crossover detected, executing main logic.")
            main_logic()
        else:
            logging.info("No MA crossover detected, checking again...")

        # Wait before fetching new data
        time.sleep(1)  # Adjust as needed

# Main logic
def main_logic():
    lot_size = 0.01
    continue_trade_logic = True
    open_buy = False
    open_sell = False
    open_tick_bid, open_tick_ask = get_tick(symbol)
    if open_tick_bid is None or open_tick_ask is None:
        logging.error("Failed to retrieve initial tick data, terminating logic.")
        return

    logging.info(f"Initial Tick Bid: {open_tick_bid} \t Initial Tick Ask: {open_tick_ask}")

    while continue_trade_logic:
        unrealized_pnl = 0.0
        open_positions = [position for position in mt5.positions_get() if position.symbol == symbol]
        total_positions = len(open_positions)
        tick_bid, tick_ask = get_tick(symbol)

        if tick_bid is None or tick_ask is None:
            logging.error("Failed to retrieve tick data, retrying...")
            time.sleep(1)
            continue

        if total_positions >= 1:
            for position in open_positions:
                unrealized_pnl += position.profit
            if total_positions >= 1 and unrealized_pnl >= 1.20:
                logging.info("Profit Reached")
                while True:
                    if not [position for position in mt5.positions_get() if position.symbol == symbol]:
                        logging.info("No open positions on gold, restarting main logic...")
                        check_time_and_display_message()
                        break
                    else:
                        for position in open_positions:
                            logging.info("Detected open trade on gold, closing...")
                            close_positions(position, symbol)
                            time.sleep(0.500)

        if tick_bid <= open_tick_bid - 0.20 and not open_sell:
            logging.info("Sell Order")
            trade_price = tick_bid
            order_type = mt5.ORDER_TYPE_SELL
            stop_loss = trade_price + 13.70
            take_profit = trade_price - 12.00

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": trade_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 6102024,
                "comment": "Minero Gold Sell",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,   
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                lot_size += 0.01
                logging.info("Order placed successfully")
                open_buy = False
                open_sell = True
            else:
                logging.error("Failed to place order. Error:", result.comment)

        elif tick_ask >= open_tick_ask + 0.20 and not open_buy:
            logging.info("Buy Order")
            trade_price = tick_ask
            order_type = mt5.ORDER_TYPE_BUY
            stop_loss = trade_price - 13.70
            take_profit = trade_price + 12.00

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot_size,
                "type": order_type,
                "price": trade_price,
                "sl": stop_loss,
                "tp": take_profit,
                "deviation": 20,
                "magic": 6102024,
                "comment": "Minero Gold Buy",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,   
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                lot_size += 0.01
                logging.info("Order placed successfully")
                open_buy = True
                open_sell = False
            else:
                logging.error("Failed to place order. Error:", result.comment)

# Initialize and start main logic
if not mt5.initialize():
    logging.error("Failed to initialize MetaTrader 5")
else:
    logging.info("Connected to MetaTrader 5")
    if HASH_1 != HASH_1 or HASH_2 != HASH_2 or HASH_3 != HASH_3:
        while True:
            logging.error("Access Denied!")
    else:
        if __author__ != "Prince Mercado" or __version__ != "08.11" or __copyright__ != "(c) 2024 Prince Mercado":
            while True:
                logging.error("Credentials Tampered!")
        else:
            check_time_and_display_message()