# 用 ledger 管理 ckb 地址

## 给 ckb-cli 安装 ledger 插件

* 安装 [ckb-cli](https://github.com/dotbitHQ/ckb-cli/tree/das-cli)
* 安装 ledger 插件
  ```bash
  git clone https://github.com/obsidiansystems/ckb-plugin-ledger.git
  cd ckb-plugin-ledger
  git checkout master
  cargo build
  ckb-cli plugin install --binary-path "$PWD/target/debug/ckb-plugin-ledger"
  ```



## 给 ledger 安装 ckb app
* 参考 [文章](https://www.reddit.com/r/NervosNetwork/comments/n1fzpt/how_do_i_secure_my_nervos_ckb_with_a_ledger_nano/) 安装 app
* 进入 app，设置允许签名 `Allow Sign Hash` 为 `ON`
* 创建一个 ckb 地址

## 将 ledger 里的 ckb 地址导入到 ckb-cli
* 用数据线连接 ledger 和本机
* 依次执行下列命令
  ```bash
  ckb-cli account list
  ## 正常情况会有如下输出：
  #- "#": 7
  #  account-id: 0x6827d9b087ffd8774b50xxxxxxxxxxae086227f187723c864dc7775bf7e046f0
  #  source: "[plugin]: ledger_plugin"
  
  ## 然后复制上述输出的 account-id ，填入下面的命令
  ckb-cli account import-from-plugin --account-id <account-id>
  
  ## 再执行一遍就会显示出 ledger 里创建的 ckb 地址了，这就说明导入成功了
  ckb-cli account list
  ```