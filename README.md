# 多签助手
本项目主要用于处理 ckb 的多签交易，分为 client 端和 server 端。
client 是指多签的各方，任何一方都可以使用 client 端发起一笔多签交易。
server 端主要是用于同步签名内容、整合各方的签名结果，并发送最终的合法交易。

## client
### 依赖
* [ckb-cli](https://github.com/dotbitHQ/ckb-cli/tree/das-cli) (与本项目放到同级目录)
  ``` bash
  git clone https://github.com/dotbitHQ/ckb-cli.git
  git checkout das-cli
  cargo build --release
  # 新的 ckb-cli 会生成在 target/release 目录 
  ```
* python3

_client 虽然不需要搭建 [das-register](https://github.com/dotbitHQ/das-register) >= v1.1.2，但需要与其做交互_

### 安装
``` bash
git clone https://github.com/pranksteess/multi_sign_tool.git
cd multi_sign_tool
pip3 install -r requirements.txt
```

### 使用
先修改 multi\_sign\_client.py 里的 `CKB_CLI` 为本地 ckb-cli 的路径

_如果本地处于离线状态，那么就需要使用 -s 参数让别人来协助推送 sig_

``` bash
python3 multi_sign_client.py

-h or help:
	Display this

-f or --tx-file:
	The CKB tx json, which need to be signed

-s or --sig:
	Help others to push their sig to server

-m or --message:
	The digest from CKB tx json

-c or --comment:
	Attach some description about this tx
```
* `-f` 后面跟上 CKB 交易的 json 文件。一般是多签的发起方使用
* `-s` 跟上签完名后的 signature 。这个参数适用的场景是：当其中一个多签用户因为种种原因连接不了 CKB 节点，他可以本地签名，然后将 signature 发给其他能连上节点的人，其他人用这个参数帮忙递交 signature
* `-m` 后面是 digest message 参数，从 lark 客户端或其他 client 端获取。这个参数一般是多签非发起方使用
* `-c` 当需要给当前这笔交易添加一些解释说明的时候可以用这个参数，记得加上双引号


_本项目允许使用 ledger 作为 client 端，需要参照 [文档](https://github.com/pranksteess/multi_sign_tool/blob/main/Howtouseledgercontrolckbaddress.md) 做好相应的设置即可_


## server
### 依赖
* [ckb-cli](https://github.com/dotbitHQ/ckb-cli/tree/das-cli) (与本项目放到同级目录)
  ``` bash
  git clone https://github.com/dotbitHQ/ckb-cli.git
  git checkout das-cli
  cargo build --release
  # 新的 ckb-cli 会生成在 target/release 目录 
  ```
* [ckb-node](https://github.com/nervosnetwork/ckb) >= v0.101.3 (参照项目文档说明搭建节点即可)
* python3

### 安装
``` bash
git clone https://github.com/pranksteess/multi_sign_tool.git
cd multi_sign_tool
pip3 install -r requirements.txt
```
### 运行
``` bash
./multi_sign_server_monitor.sh
```
然后在 crontab 里加入监控命令（或者用 supervisor 等第三方工具管理）
``` bash
crontab -e
*/10 * * * * sh -c /xxx/xxx/multi_sign_tool/multi_sign_monitor.sh >> /xxx/xxx/multi_sign_tool/monitor.log 2>&1
```
如果 server 是 macos 的，它的 crontab 运行可能会报一些权限错误，可以参照 [这里](https://onns.xyz/blog/2020/06/10/fix-crontab-operation-not-permitted-on-mac/) 尝试修复
