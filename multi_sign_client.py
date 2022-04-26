import pexpect
import requests
import json
import getopt
import sys
import os

CKB_CLI = os.getcwd() + "/../ckb-cli/target/release/ckb-cli"

DEBUG = False
SIGN_SVR_IP = "100.77.204.22"
SIGN_SVR_PORT = "8000"

SIGN_SVR_API_URL = "http://" + SIGN_SVR_IP + ":" + SIGN_SVR_PORT
CKB_CLI_HOME = "CKB_CLI_HOME=~/.ckb-cli"

TMP_TX_FILE = "./tmp_tx.json"

CMD_PREFIX = CKB_CLI_HOME + " " + CKB_CLI + " "

COMMENT = ""
DIGEST_MESSAGE = ""
TX_FILE = ""
SIGNATURE = ""

F_MSG = 1
F_FILE = 2
F_SIG = 3

def log(text=""):
	def decorator(func):
		def wrapper(*args, **kw):
			if DEBUG:
				print(">>> %sbegin: %s >>>" % (text, func.__name__))
			result = func(*args, **kw)
			if DEBUG:
				print("<<< %send: %s <<<" % (text, func.__name__))
			return result
		return wrapper
	if not isinstance(text, str):
		return decorator(text)
	return decorator

def save_to_file(json_obj, file_path):
	tmp = file_path
	f = open(tmp, 'w')
	f.write(json.dumps(json_obj, indent=4))
	f.close()


@log()
def send_bit_register_request(path, body):
	try:
		global BIT_REGISTER_HOST
		response = requests.post(
			url="https://" + BIT_REGISTER_HOST + path,
			headers={
				"￼￼accept": "application/json, text/plain, */*",
				"￼￼accept-encoding": "gzip, deflate, br",
				"￼￼accept-language": "en-US,en;q=0.9",
				"￼￼cache-control": "no-cache",
				"￼￼content-type": "application/json",
				"￼￼origin": "https://data.did.id",
				"￼￼pragma": "no-cache",
				"￼￼referer": "https://
                                data.did.id/",
				"￼￼sec-ch-ua": "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"100\", \"Google Chrome\";v=\"100\"",
				"￼￼sec-ch-ua-mobile": "?0",
				"￼￼sec-ch-ua-platform": "\"macOS\"",
				"￼￼sec-fetch-dest": "empty",
				"￼￼sec-fetch-mode": "cors",
				"￼￼sec-fetch-site": "same-site",
				"￼￼user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36",
				"Content-Type": "application/json; charset=utf-8",
			},
			data=json.dumps(body)
		)
		# print('Response HTTP Status Code: {status_code}'.format(status_code=response.status_code))
		# print('Response HTTP Response Body: {content}'.format(content=response.content))
                res_obj = json.loads(response.content)
                if res_obj["err_no"] == 0:
                        global TMP_TX_FILE
                        file_name = path[path.rfind('/')+1:]
                        TMP_TX_FILE = "./" + file_name
                        save_to_file(res_obj["data"], TMP_TX_FILE)
		return res_obj["err_no"]
	except requests.exceptions.RequestException:
		print('HTTP Request failed')

@log()
def send_edit_role(account, role="owner"):
	path = "/v1/account/edit/" + role
	body = {
		"account": account,
		"raw_param": {
			"manager_chain_type": 1,
			"manager_address": "0x773BCCE3B8b41a37CE59FD95F7CBccbff2cfd2D0"
		},
		"evm_chain_id": 137,
		"chain_type": 3,
		"address": "TUN2FJuiy6BXac4qnCLTsrMxrUqD9JBhdH"
	}
	return send_bit_register_request(path, body)

@log()
def send_sig_args(sig, args="", digest=""):
	try:
		global SIGN_SVR_API_URL, TX_FILE, COMMENT
		file_name = TX_FILE[TX_FILE.rfind('/')+1:]
		print("file_name: " + file_name)
		response = requests.post(
			url = SIGN_SVR_API_URL,
			headers = {
				"Content-Type": "application/json",
			},
			data = json.dumps({
				"action": "sign",
				"args": args,
				"sig": sig,
				"digest": digest,
				"contract_name": file_name,
				"comment": COMMENT
			})
		)
		res = json.loads(response.content)
		#print(res)
		return res
	except requests.exceptions.RequestException:
		print('HTTP Request failed')

@log()
def exe_shell(cmd, need_json=False):
	if need_json:
		cmd.extend(["--output-format json --no-color "])
	else:
		cmd.extend(["--no-color "])

	res = ""
	cmd_line = ' '.join(cmd)
	args_list = ["-c", cmd_line]
	#print("cmd: " + cmd_line)
	child = pexpect.spawn("/bin/sh", args_list, timeout=120)
	index = child.expect(['Pass', pexpect.EOF, pexpect.TIMEOUT], timeout=120)
	if index == 0:
		#child.sendline(pwd)
		res = child.read()
	if index == 1:
		res = child.before
	if index == 2:
		print("das-tool timeout with full cmd: %s" % ' '.join(cmd))
		return res, ""
	res = res.decode("utf8")
	child.close()

	#print("cmd result: " + res)
	digest_msg = ""
	if need_json:
		tmp_json = json.loads(res)
		return tmp_json, digest_msg
	else:
		origin_list = res.split('\n')
		if len(origin_list) < 2:
			print(origin_list)
			raise RuntimeError("origin_list len < 2")

		origin = origin_list[-2].replace("\r", "")
		# result_str = origin[5:-4] if need_color_strip else origin
		result_str = origin
		for line in origin_list:
			#print("line: " + line)
			if "digest-message: " in line:
				print("\n~~~~~~~~~~~ FOR MULTI SIGN ~~~~~~~~~~~")
				print(line)
				digest_msg = line.split(" ")[2].strip()
				print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")
		return result_str, digest_msg

def usage():
	print(
		"-h or help: \n\tDisplay this\n\n" \
		"-f or --tx-file: \n\tThe CKB tx json, which need to be signed\n\n" \
		"-s or --sig: \n\tHelp others to push their sig to server\n\n" \
		"-m or --message: \n\tThe digest from CKB tx json\n\n" \
		"-c or --comment: \n\tAttach some description about this tx"
	)

def args_handle():
	global COMMENT, DIGEST_MESSAGE, TX_FILE, SIGNATURE, F_MSG, F_FILE, F_SIG
	ret = 0
	try:
		options, args = getopt.getopt(sys.argv[1:], "hm:f:s:c:", ["help", "message=", "tx-file=", "sig=", "comment="])
		#print(options)
		if len(options) == 0:
			ret = usage()
			return ret
		for name, value in options:
			if name in ('-h', '--help'):
				ret = usage()
				return ret
			elif name in ('-m', '--message'):
				DIGEST_MESSAGE = value
				ret = F_MSG
			elif name in ('-f', '--tx-file'):
				TX_FILE = value
				ret = F_FILE
			elif name in ('-s', '--sig'):
				SIGNATURE = value
				ret = F_SIG
			elif name in ('-c', '--comment'):
				COMMENT = value
			else:
				ret = usage()
				return ret

	except:
		ret = usage()
		return ret
	return ret

@log()
def get_muli_account():
	global CMD_PREFIX
	cmd = CMD_PREFIX + " account list "
	account_list = exe_shell([cmd], need_json=True)
	for iitem in account_list:
		for item in iitem:
			if "ledger_plugin" in item["source"] and item.get("lock_arg", "") != "":
				return 0, item["lock_arg"]
	return -1, "please import account from ledger first"

@log()
def get_args():
	ret, account_args = get_muli_account()
	if ret != 0:
		print("error msg: " + account_args)
		return ""
	return account_args

@log()
def get_digest(account_args):

	global CMD_PREFIX, TX_FILE
	#print("account_args: " + account_args)
	cmd = CMD_PREFIX + " tx sign-inputs --add-signatures" +\
		" --from-account " + account_args +\
		" --tx-file " + TX_FILE +\
		" --only-digest"

	res_str, digest_msg = exe_shell([cmd])
	if len(digest_msg) == 64:
		return digest_msg
	else:
		print("error in digest: " + digest_msg)
		print("error msg: " + res_str)
		return ""

@log()
def get_sig_args(digest=""):
	global CMD_PREFIX

	account_args = get_args()
	if account_args == "":
		print("args is empty")
		return -1, "", "", ""

	if digest == "":
		digest = get_digest(account_args)
		if digest == "":
			print("digest is empty")
			return -1, "", "", ""

	cmd = CMD_PREFIX + " util sign-message --recoverable" +\
		" --from-account " + account_args +\
		" --message " + digest

	res_str, _ = exe_shell([cmd])
	sig = res_str.split(" ")[1].strip()
	if len(sig) != 132:
		print("error in sig: " + res_str)
		return -1, "", "", ""
	return 0, sig, account_args, digest

@log()
def sign(_type):
	global SIGNATURE, F_MSG, F_FILE, F_SIG, DIGEST_MESSAGE
	sig = SIGNATURE
	digest = ""
	args = ""
	ret = 0
	if _type != F_SIG:
		if _type == F_MSG:
			digest = DIGEST_MESSAGE

		ret, sig, args, digest = get_sig_args(digest)
		if ret != 0:
			return -1
	print("sig: %s, args: %s, digest: %s" % (sig, args, digest))
	res = send_sig_args(sig, args, digest)
	print(res)
	# will return -1 even if send msg to lark successfully
	if res.get("ret", -1000) != 0 and res.get("ret", -1000) != -1:
		print("error in response: " + json.dumps(res))
		return -1
	print("successfully sent")
	return 0


def main():
	global F_MSG, F_FILE, F_SIG
	ret = args_handle()
	if ret in [F_MSG, F_FILE, F_SIG]:
		sign(ret)

if __name__ == '__main__':
	main()


