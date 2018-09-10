# HiveMiner #
A simple CoinHive miner using [libcryptohive](https://github.com/EZForever/libcryptohive).
  
## Usage ##
*Important note:  
This thing is just a test to see if my lib works, I do not guarantee that it is bug-free or could run correctly.  
It is not suitable for business mining due to it's AWFUL speed (60hashes/s vs 1hash/s).*  
1. `pip install websocket-client`
2. Get libcryptohive (link above) and compile it
3. Modify `HiveMiner.py`, change `SITEKEY` and `LIBCH` as you wish
4. `python HiveMiner.py`
A half-complete CoinHive protocol example is also presented (see `CoinHiveProtocol.json`)
  
## License ##
[GLWTPL](https://github.com/me-shaon/GLWTPL/blob/master/LICENSE)  