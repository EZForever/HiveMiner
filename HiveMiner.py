import threading
import os
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

#Number of worker threads (depends on your CPU by default)
THREADS = int(os.cpu_count() / 2) #FIXME: How to get physical core number?

#Show [D] outputs
DEBUG = False

#Show websocket traces
#You might want to redirect output to elsewhere if set to True
TRACE = False

#Current CoinHive JS Version (CoinHive.VERSION)
CHVERSION = 9

#Server list from CoinHive JS (CoinHive.CONFIG.WEBSOCKET_SHARDS)
CHSERVERS = [
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
  "jobChanged": 0
}

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
      for i in range(len(target)):
        targetFull[len(targetFull) - i - 1] = target[len(target) - i - 1]
      for i in range(len(targetFull) - len(target)):
        targetFull[i] = 0xff
    else:
      targetFull = target
    if DEBUG:
      print("[D][SVR] blob = " + MsgData["params"]["blob"])
      print("[D][SVR] target = " + binascii.hexlify(targetFull).decode())
    Job = {
      "job_id": MsgData["params"]["job_id"],
      "blob": binascii.unhexlify(MsgData["params"]["blob"]),
      "target": targetFull,
      "jobChanged": (1 << THREADS) - 1
    }

  elif MsgData["type"] == "verify":
    print("[I][SVR] Verify requested")
    if DEBUG:
      print("[D][SVR] blob = " + MsgData["params"]["blob"])
      print("[D][SVR] nonce = " + MsgData["params"]["nonce"])
      print("[D][SVR] result = " + MsgData["params"]["result"])
    #Server requires us to send a verified packet
    Ret = {
      "type": "verified",
      "params": {
        "verify_id": MsgData["params"]["verify_id"],
        "verified": True,
        "result": MsgData["params"]["result"]
      }
    }
    QSend.put(Ret)

  else:
    print("[W][SVR] Unknown message " + Msg)

  return

def MeetsTarget(result, target):
  #Translated from CoinHive's CryptonightWASMWrapper.prototype.meetsTarget
  for i in range(len(target)):
    ri = len(result) - i - 1
    ti = len(target) - i - 1
    if result[ri] > target[ti]: return False
    elif result[ri] < target[ti]: return True
  return False

def WorkerFunc(WorkerNo):
  global Job
  print("[I][CLI] %d: Worker thread ready" % WorkerNo)
  while Job["job_id"] == "": time.sleep(0.1)

  try:
    ctypes.cdll.LoadLibrary(LIBCH)
    libch = ctypes.cdll.libcryptohive
    libch.cryptohive_create()
    libch.cryptohive_pInput.restype = ctypes.POINTER(ctypes.c_char * 84)
    libch.cryptohive_pOutput.restype = ctypes.POINTER(ctypes.c_char * 32)
    blob = libch.cryptohive_pInput().contents
    result = libch.cryptohive_pOutput().contents
  except:
    print("[F][CLI] %d: libCryptoHive could not be initialized" % WorkerNo)
    return
  if DEBUG: print("[D][CLI] %d: libCryptoHive initialized from %s" % (WorkerNo, LIBCH))

  while True:
    if Job["jobChanged"] & 1 << WorkerNo:
      if DEBUG: print("[D][CLI] %d: New job" % WorkerNo)

      for i in range(len(Job["blob"])): blob[i] = Job["blob"][i]

      #type(blob[0]) == bytes, type(blob[0][0]) == int
      if blob[0][0] > 7:
        Hash = libch.cryptohive_hash_v2_Q
      elif blob[0][0] == 7:
        Hash = libch.cryptohive_hash_v1_Q
      else:
        Hash = libch.cryptohive_hash_v0_Q

      Job["jobChanged"] &= ~(1 << WorkerNo)

    nonce = random.randint(0, 0xffffffff).to_bytes(length = 4, byteorder = "big")
    for i in range(4):
      blob[i + 39] = nonce[i]

    Hash()

    if MeetsTarget(result.raw, Job["target"]):
      print("[I][CLI] %d: Hash found" % WorkerNo)
      if DEBUG:
        print("[D][CLI] nonce = " + binascii.hexlify(nonce).decode())
        print("[D][CLI] result = " + binascii.hexlify(result).decode())
      Ret = {
        "type":"submit",
        "params": {
          "version": CHVERSION,
          "job_id": Job["job_id"],
          "nonce": binascii.hexlify(nonce).decode(),
          "result": binascii.hexlify(result).decode()
        }
      }
      QSend.put(Ret)
  try:
    libch.cryptohive_destroy()
  except:
    pass
  print("[I][CLI] %d: Worker thread stopped" % WorkerNo)

def WSRecvFunc():
  global SocketWS
  print("[I][WS] Recv thread started")
  try:
    Server = random.choice(CHSERVERS)
    print("[I][WS] Chosen server is " + Server)
    SocketWS.connect(Server)
  except:
    print("[E][WS] Connect failed, end thread")
    return
  print("[I][WS] Connected")

  Workers = [None] * THREADS
  for i in range(THREADS):
    Workers[i] = threading.Thread(name = "Worker %d" % i, target = WorkerFunc, args = (i, ))
    Workers[i].setDaemon(True)
    Workers[i].start()

  Ret = {
    "type": "auth",
    "params": {
      "version": CHVERSION,
      "site_key": SITEKEY,
      "type": "anonymous",
      "user": None,
      "goal": 0,
    }
  }
  QSend.put(Ret)

  while True:
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
  global SocketWS
  print("[I] HiveMiner Dev - Running with %d threads" % THREADS)
  print("[I] For testing purposes only - it's unstable")
  if TRACE: websocket.enableTrace(True)

  if not THREADS:
    print("[F][WS] No usable core. Please change THREADS to a constant.")
    return

  WSRecv = threading.Thread(name = "WSRecv", target = WSRecvFunc)
  WSRecv.setDaemon(True)
  WSRecv.start()

  try:
    print("[I][WS] Send thread ready")
    while WSRecv.isAlive():
      try:
        Msg = json.dumps(QSend.get(block = False))
      except queue.Empty:
        time.sleep(0.1)
        continue
      try:
        SocketWS.send(Msg.encode(encoding = "ascii"))
        if DEBUG: print("[D][WS] SEND " + Msg)
      except:
        print("[E][WS] SEND FAILED" + Msg)
  except KeyboardInterrupt:
    print("[I] ^C Received")
  quit(0)

if __name__ == "__main__":
  main()