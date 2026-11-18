"""Single source of truth for the live tape config.

Both build_site.py and build_static.py import TAPE_CFG from here, so a ticker
symbol fix lands once instead of twice (the second instance regressed hard:
TVC:DXY / TVC:VIX reverted to "Invalid symbol" on /terms.html and /about/ while
story pages had already moved to CAPITALCOM). Keep this the ONLY place the
symbol list is defined.
"""
TAPE_CFG = {
    "symbols": [
        {"proName": "CAPITALCOM:SPX500", "title": "S&P 500"},
        {"proName": "FOREXCOM:NSXUSD", "title": "Nasdaq 100"},
        {"proName": "TVC:GOLD", "title": "Gold"},
        {"proName": "TVC:USOIL", "title": "WTI"},
        {"proName": "BITSTAMP:BTCUSD", "title": "BTC"},
        {"proName": "FX:EURUSD", "title": "EUR/USD"},
        {"proName": "CAPITALCOM:DXY", "title": "Dollar Index"},
        {"proName": "CAPITALCOM:VIX", "title": "VIX"},
    ],
    "showSymbolLogo": False,
    "colorTheme": "dark",
    "isTransparent": True,
    "displayMode": "compact",
    "locale": "en",
}
