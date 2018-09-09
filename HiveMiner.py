import threading
import ctypes
import time
import random
import binascii
import json
import websocket
import queue

#Site-key
SITEKEY = "9Dvc7G3HNoQooy922EzrHY5cdK57QOqP"

#Name of (or path to) libcryptohive
LIBCH = "libcryptohive.dll"
#LIBCH = "libcryptohive.so"

#Show [D] outputs
DEBUG = False

#Show websocket traces
#You might want to redirect output to elsewhere if set to True
TRACE = False

#Server list from CoinHive JS
SERVERS = [
  "wss://ws001.coinhive.com/proxy", "wss://ws002.coinhive.com/proxy", "wss://ws003.coinhive.com/proxy", "wss://ws004.coinhive.com/proxy",
  "wss://ws005.coinhive.com/proxy", "wss://ws006.coinhive.com/proxy", "wss://ws007.coinhive.com/proxy", "wss://ws008.coinhive.com/proxy",
  "wss://ws009.coinhive.com/proxy", "wss://ws010.coinhive.com/proxy", "wss://ws011.coinhive.com/proxy", "wss://ws012.coinhive.com/proxy",
  "wss://ws013.coinhive.com/proxy", "wss://ws014.coinhive.com/proxy", "wss://ws015.coinhive.com/proxy", "wss://ws016.coinhive.com/proxy",
  "wss://ws017.coinhive.com/proxy", "wss://ws018.coinhive.com/proxy", "wss://ws019.coinhive.com/proxy", "wss://ws020.coinhive.com/proxy",
  "wss://ws021.coinhive.com/proxy", "wss://ws022.coinhive.com/proxy", "wss://ws023.coinhive.com/proxy", "wss://ws024.coinhive.com/proxy",
  "wss://ws025.coinhive.com/proxy", "wss://ws026.coinhive.com/proxy", "wss://ws027.coinhive.com/proxy", "wss://ws028.coinhive.com/proxy",
  "wss://ws029.coinhive.com/proxy", "wss://ws030.coinhive.com/proxy", "wss://ws031.coinhive.com/proxy", "wss://ws032.coinhive.com/proxy"
]

SocketWS = websocket.WebSocket()
QSend = queue.Queue()
Job = {
  "job_id": "",
  "blob": b"",
  "target": b"",
  "jobChanged": False
}

EndFlag = True

def ProcSvr(Msg):
  global Job
  MsgData = json.loads(Msg)

  if MsgData["type"] == "error":
    print("[E][SVR] CoinHive Error: " + MsgData["params"]["error"])

  elif MsgData["type"] == "banned":
    print("[E][SVR] Banned. Oops.")

  elif MsgData["type"] == "invalid_msg":
    print("[E][SVR] Invalid message!? What am I sending?")

  elif MsgData["type"] == "invalid_hash":
    print("[E][SVR] Invalid hash. Things are going worse.")

  elif MsgData["type"] == "authed":
    print("[I][SVR] Authed")

  elif MsgData["type"] == "hash_accepted":
    print("[I][SVR] Hash Accepted %d" % MsgData["params"]["hashes"])

  elif MsgData["type"] == "job":
    print("[I][SVR] Got job")
    target = binascii.unhexlify(MsgData["params"]["target"])
    targetFull = bytearray(8)
    if len(target) <= 8:
      for i in range(0, len(target)):
        targetFull[len(targetFull) - i - 1] = target[len(target) - i - 1]
      for i in range(0, len(targetFull) - len(target)):
        targetFull[i] = 0xff
    else:
      targetFull = target
    #if DEBUG: print("[D][SVR] target = " + binascii.hexlify(targetFull).decode())
    Job = {
      "job_id": MsgData["params"]["job_id"],
      "blob": binascii.unhexlify(MsgData["params"]["blob"]),
      "target": targetFull,
      "jobChanged": True
    }

  elif MsgData["type"] == "verify":
    print("[I][SVR] Verify requested")
    #Server requires us to send a verify packet
    #Or it will ban us (maybe)
    Ret = {
      "type": "verified",
      "params": {
        verify_id: MsgData["params"]["verify_id"], #BUG: NameError: name 'verify_id' is not defined
        verified: True,
        result: MsgData["params"]["result"]
      }
    }
    QSend.put(Ret)

  else:
    print("[W][SVR] Unknown message " + Msg)

  return

def MeetsTarget(result, target):
  #Translated from CoinHive's CryptonightWASMWrapper.prototype.meetsTarget
  for i in range(0, len(target)):
    ri = len(result) - i - 1
    ti = len(target) - i - 1
    if result[ri] > target[ti]: return False
    elif result[ri] < target[ti]: return True
  return False

def WorkerFunc():
  global Job
  print("[I][CLI] Worker thread ready")
  while Job["job_id"] == "": time.sleep(0.1)

  try:
    ctypes.cdll.LoadLibrary(LIBCH)
    libch = ctypes.cdll.libcryptohive
    libch.cryptohive_create() #TODO: Where to libch.cryptohive_destroy() ?
  except:
    print("[F][CLI] libCryptoHive could not be initialized")
    return
  print("[I][CLI] libCryptoHive initialized from " + LIBCH)

  result = ctypes.create_string_buffer(32)
  while EndFlag:
    if Job["jobChanged"]:
      print("[I][CLI] New job")
      blob = ctypes.create_string_buffer(len(Job["blob"]))
      for i in range(0, ctypes.sizeof(blob)): blob[i] = Job["blob"][i]
      #if DEBUG: print("[D][CLI] blob = " + binascii.hexlify(blob.raw).decode())
      if blob[i] == 7:
        Hash = libch.cryptohive_hash_v1
      else:
        Hash = libch.cryptohive_hash_v0
      Job["jobChanged"] = False

    nonce = random.randint(0, 0xffffffff).to_bytes(length = 4, byteorder = "little")
    #if DEBUG: print("[D][CLI] nonce = " + binascii.hexlify(nonce).decode())
    for i in range(0, 3):
      blob[i + 39] = nonce[i]
    Hash(ctypes.byref(blob), ctypes.byref(result), ctypes.sizeof(blob));
    #if DEBUG: print("[D][CLI] result = " + binascii.hexlify(result.raw).decode())

    if MeetsTarget(result.raw, Job["target"]):
      print("[I][CLI] Hash found")
      Ret = {
        "type":"submit",
        "params": {
          "version": 7,
          "job_id": Job["job_id"],
          "nonce": binascii.hexlify(nonce).decode(),
          "result": binascii.hexlify(result.raw).decode()
        }
      }
      QSend.put(Ret)
  print("[I][CLI] Worker thread stopped")

def WSRecvFunc():
  global SocketWS
  print("[I][WS] Recv thread started")
  try:
    Server = random.choice(SERVERS)
    print("[I][WS] Chosen server is " + Server)
    SocketWS.connect(Server)
  except:
    print("[E][WS] Connect failed, end thread")
    return
  print("[I][WS] Connected")

  Worker = threading.Thread(name = "Worker", target = WorkerFunc)
  Worker.setDaemon(True)
  Worker.start()

  Ret = {
    "type": "auth",
    "params": {
      "version": 7,
      "site_key": SITEKEY,
      "type": "anonymous",
      "user": None,
      "goal": 0,
    }
  }
  QSend.put(Ret)

  while EndFlag:
    try:
      Msg = SocketWS.recv()
    except:
      break
    if not Msg: break
    if DEBUG: print("[D][WS] RECV " + Msg)
    ProcSvr(Msg)

  try:
    SocketWS.close()
  except:
    pass
  print("[I][WS] Recv thread stopped")

def main():
  global SocketWS, EndFlag
  print("[I] libCH-Miner v0.0.1 Dev")
  print("[I] For testing purposes only - it's too slow")
  if TRACE: websocket.enableTrace(True)
  WSRecv = threading.Thread(name = "WSRecv", target = WSRecvFunc)
  WSRecv.setDaemon(True)
  WSRecv.start()
  try:
   print("[I][WS] Send thread ready")
   while WSRecv.isAlive():
     Msg = json.dumps(QSend.get())
     try:
       SocketWS.send(Msg.encode(encoding = "ascii"))
       if DEBUG: print("[D][WS] SEND " + Msg)
     except:
       print("[E][WS] SEND FAILED" + Msg)
  except KeyboardInterrupt:
    print("[I] ^C Received")
  EndFlag = False
  quit(0)

if __name__ == "__main__":
  main()