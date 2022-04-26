# 多签助手
## client
### 依赖

* [ckb-cli](https://github.com/dotbitHQ/ckb-cli/tree/das-cli) (与本项目放到同级目录)
  ``` bash
  git clone https://github.com/dotbitHQ/ckb-cli.git
  git checkout das-cli
  cargo build --release
  # 新的 ckb-cli 会生成在 target/release 目录 
  ```
* [ckb-node](https://github.com/nervosnetwork/ckb) >= v0.101.3 (参照项目文档说明搭建节点即可)
* [das-register](https://github.com/dotbitHQ/das-register) >= v1.1.2
* python3

### 安装
``` bash
git clone https://github.com/pranksteess/multi_sign_tool.git
cd multi_sign_tool
pip3 install -r requirements.txt
```

### 使用
先修改 multi\_sign\_client.py 里的 `CKB_CLI` 为本地 ckb-cli 的路径

_如果本机处于离线状态，那么就需要使用 -s 参数让别人来协助推送 sig_

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


### client 端为 ledger 的情况
首先需要参照 [文档](https://github.com/pranksteess/Howtouseledgercontrolckbaddress.md) 设置好用 ledger 管理 ckb 地址

正常情况下，只需要操作一次 ledger，但多签发起方有可能会签两次。

第一次是为了获取 digest，第二次才是真正签名 digest 获得 signature。

之所以是`可能`，这是因为 ledger 的 nervos app 有个 bug，当 CKB 交易 json 太大时，第一次直接签名 json 文件会报错，由于 client 脚本兼容了这种错误，所以这种情况就没有`第一次签名`的过程

__update: 签两次的问题已经在本项目这一层兼容并修复了，现在每次发起只会签一次__

## server
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
