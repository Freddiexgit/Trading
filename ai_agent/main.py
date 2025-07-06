from Config import DEFAULT_CONFIG
from trading_graph import TradingAgentsGraph





config = DEFAULT_CONFIG.copy()

graph = TradingAgentsGraph(
    ["market"], config=config, debug=True
)

