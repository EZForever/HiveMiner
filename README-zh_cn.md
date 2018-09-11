# HiveMiner #
使用 [libcryptohive](https://github.com/EZForever/libcryptohive) 实现的CoinHive挖矿程序
  
## 使用方法 ##
*注意：  
本程序仅用于个人测试用途，开发者不保证程序是否存在BUG或是否能稳定运行。  
考虑到不稳定因素，本程序不适用于商业挖矿。*  
1. `pip install websocket-client`
2. 下载libcryptohive的源码（链接见上）并编译
3. 修改 `HiveMiner.py` 中的 `SITEKEY` 和 `LIBCH` 为自己想要的值
4. `python HiveMiner.py`  
一份不完整的CoinHive协议参考参见 `CoinHiveProtocol.json`
  
## 开源许可 ##
[GLWTPL](https://github.com/me-shaon/GLWTPL/blob/master/LICENSE_zh-CN)  
