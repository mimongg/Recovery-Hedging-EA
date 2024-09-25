import MetaTrader5 as mt5
import time
from datetime import datetime

#Close positions working
#Opening trades successfully 
#Adjust zoning depending on market volume and TP prices
symbol = "XAUUSD"

def check_time_and_display_message():
    while True:
        current_time = datetime.now().time()  # Get the current time

        start_time = current_time.replace(hour=13, minute=0, second=0, microsecond=0)  # 1 PM
        end_time = current_time.replace(hour=22, minute=0, second=0, microsecond=0)    # 10 PM

        # Check if the current time is within the range
        if start_time <= current_time <= end_time:
            print("Session Activated!")
            main_logic()
            break
        else:
            print("It's not between 1 PM and 10 PM.")
            time.sleep(1)

def get_tick(symbol):
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"Failed to retrieve tick data for symbol {symbol}!")
        return None, None
    return tick.bid, tick.ask

def close_positions(position):
    tick = mt5.symbol_info_tick(position.symbol)
    
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "position": position.ticket,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_BUY if position.type ==1 else mt5.ORDER_TYPE_SELL,
        "price": tick.ask if position.type == 1 else tick.bid,
        "deviation": 20,
        "magic": 100,
        "comment": "python script close",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result

def main_logic():
    lot_size = 0.01
    continue_trade_logic = True
    open_buy = False
    open_sell = False
    open_tick_bid, open_tick_ask = get_tick("XAUUSD")
    print(f"Tick Bid: {open_tick_bid} \t Tick Ask: {open_tick_ask}")
    
    while continue_trade_logic:
        unrealized_pnl = 0.0
        open_positions = mt5.positions_get()
        total_positions = mt5.positions_total()
        tick_bid, tick_ask = get_tick("XAUUSD")
        if total_positions >= 1:
            for position in open_positions:
                unrealized_pnl += position.profit
            if unrealized_pnl >= 1.00 * total_positions:
                print("Profit Reached")
                while True:
                    if not mt5.positions_get():
                        print("No open positions, restarting main logic...")
                        check_time_and_display_message()
                        break
                    else:
                        for position in open_positions:
                            print("Detected open trade, closing...")
                            close_positions(position)
                            time.sleep(0.500)
        
        if tick_bid <= open_tick_bid - 0.50 and not open_sell: #Sell condition
            print("Sell Order")
            trade_price = tick_bid
            order_type = mt5.ORDER_TYPE_SELL
            stop_loss = trade_price + 2.00
            take_profit = trade_price - 1.00
            
            #Order Request
            request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot_size,
                    "type": order_type,
                    "price": trade_price,
                    "sl": stop_loss,
                    "tp": take_profit,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,   
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                lot_size += 0.01
                print("Order placed successfully")
                open_buy = False
                open_sell = True
            else:
                tick_bid, tick_ask = get_tick("XAUUSD")
                print("Failed to place order. Error:", result.comment)
                
        elif tick_ask >= open_tick_ask + 0.50 and not open_buy: #Buy condition
            print("Buy Order")
            trade_price = tick_ask
            order_type = mt5.ORDER_TYPE_BUY
            stop_loss = trade_price - 2.00
            take_profit = trade_price + 1.00
            
            #Order Request ADD WHILE TRUE
            request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": symbol,
                    "volume": lot_size,
                    "type": order_type,
                    "price": trade_price,
                    "sl": stop_loss,
                    "tp": take_profit,
                    "deviation": 20,
                    "magic": 234000,
                    "comment": "python script open",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,   
            }
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                lot_size *= 2
                print("Order placed successfully")
                open_buy = True
                open_sell = False
            else:
                tick_bid, tick_ask = get_tick("XAUUSD")
                print("Failed to place order. Error:", result.comment)
            
#Initialize Main Logic
if not mt5.initialize():
    print("Failed to connect on MT5")
else:
    print("Connected to Meta Trader 5")
    check_time_and_display_message()
    

