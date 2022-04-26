# --coding:utf-8--

from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import signal
import json
import requests
import pexpect
import time

API_URL = "http://127.0.0.1:8114"
DAS_CLI = "CKB_CLI_HOME=~/.ckb-cli API_URL=" + API_URL + " /Users/park/Documents/ckb/ckb-cli/target/release/das-cli"
TX_JSON_CACHE_PATH = "/Users/park/Documents/multi_sign_cache/"
MULTI_SIGN_THRESHOLD = 3

CURRENT_CONTRACT = ""
MULTI_SIGNER_ARGS = {
	"0x567419c40d0f2c3566e7630ee32697560fa00000": "signer0",
	"0x543d8ec90d784f60cf920e76a359ae8383911111": "signer1",
	"0x14dd22136ce74aee2a007c71e5440143dab22222": "signer2",
	"0x619b019a75910e04d5f215ace571e5600d433333": "signer3",
	"0x6d6a5e1df00e2cf82dd4dcfbba444a9411944444": "signer4"
}


class RequestHandler(BaseHTTPRequestHandler):

	def exe_shell(self, cmd):
		cmd.extend(["--no-color "])
		res = ""
		cmd_line = ' '.join(cmd)
		args_list = ["-c", cmd_line]
		print("cmd: " + cmd_line)
		child = pexpect.spawn("/bin/sh", args_list, timeout=120)
		index = child.expect(['Pass', pexpect.EOF, pexpect.TIMEOUT], timeout=120)
		if index == 0:
			#child.sendline(pwd)
			res = child.read()
		if index == 1:
			res = child.before
		if index == 2:
			print("das-tool timeout with full cmd: %s" % ' '.join(cmd))
			return res
		res = res.decode("utf8")
		child.close()

		print("cmd result: " + res)
		origin_list = res.split('\n')
		origin = origin_list[-2].replace("\r", "")
		# result_str = origin[5:-4] if need_color_strip else origin
		result_str = origin
		return result_str

	def do_POST(self):
		# 解析请求 body
		req_body = self.rfile.read(int(self.headers['content-length']))
		obj = json.loads(req_body.decode("utf-8"))
		print(req_body)

		action = obj.get("action", "")
		if action == "sign":
			global CURRENT_CONTRACT
			sig = obj.get("sig", "")
			args = obj.get("args", "")
			digest = obj.get("digest", "")
			contract = obj.get("contract_name", "")
			comment = obj.get("comment", "")
			if contract != "":
				CURRENT_CONTRACT = contract
			self.handle_action_sign(sig, args, digest, CURRENT_CONTRACT, comment)

		return

	def read_from_file(self, file_path):
		with open(file_path, encoding="utf-8") as f:
			data = json.load(f)
			return data

	def save_to_file(self, json_obj, file_path):
		tmp = file_path
		f = open(tmp, 'w')
		f.write(json.dumps(json_obj, indent=4))
		f.close()

	def get_name_by_args(self, args):
		if args == "":
			return "NO_NAME"
                global MULTI_SIGNER_ARGS
		return MULTI_SIGNER_ARGS[args]

	def make_msg_for_lark(self, sig, args, digest, contract):
		name = self.get_name_by_args(args)
		msg_format = "{} have completed sign on contract {}\nsig: {}\ndigest: {}"
		msg = msg_format.format(name, contract, sig, digest)
		return name, msg

	def send_tx_file(self, file_path):
		global DAS_CLI, CURRENT_CONTRACT
		cmd = DAS_CLI + " tx send " +\
			" --tx-file " + file_path +\
			" --skip-check"
		tx_hash = self.exe_shell([cmd])
		if not tx_hash.startswith("0x") or len(tx_hash) != 66:
			return -100, tx_hash
		CURRENT_CONTRACT = ""
		return 0, tx_hash

	def get_transaction(self, tx_hash):
		global API_URL
		tx_hash = tx_hash.replace("\n", "").replace(" ", "").replace("\r", "")
		if not tx_hash.startswith("0x") or len(tx_hash) != 66:
			print("tx_hash: " + tx_hash)
			raise RuntimeError('HTTP Param Error')
		try:
			response = requests.post(
				url = API_URL,
				headers = {
					"Content-Type": "application/json",
					},
				data = json.dumps({
					"id": 1,
					"jsonrpc": "2.0",
					"method": "get_transaction",
					"params": [ tx_hash ]
					})
				)
			return json.loads(response.content)
		except requests.exceptions.RequestException:
			print('HTTP Request failed')

	def wait_for_ready(self, tx, contract_name):
		if tx == "":
			return
		tx_json = self.get_transaction(tx)

		wait_s = 10
		total_wait_s = 0
		wait_title = "WAITING"
		try:
			while tx_json["result"] == None or tx_json["result"]["tx_status"]["status"] != "committed":
				msg = "wait for {}({}) to been committed, totally waste: {}s".format(contract_name, tx, str(total_wait_s))
				self.send_message(wait_title, msg)
				time.sleep(wait_s)
				tx_json = self.get_transaction(tx)
				total_wait_s = total_wait_s + wait_s
		except:
			print(tx_json)
			raise RuntimeError("Unexcept json")

		if total_wait_s != 0:
			pre_url = "https://explorer.nervos.org/transaction/"
			msg = contract_name + " committed: " + pre_url + tx
			commit_title = "COMMITED"
			self.send_message(commit_title, msg)

		return tx_json

	def handle_action_sign(self, sig, args, digest, contract, comment):
		if sig == "":
			rsp = {"ret": -100, "msg": "sig is empty"}
			self.response(json.dumps(rsp))
			return
		if contract == "":
			rsp = {"ret": -100, "msg": "multi sign has ended or is not start"}
			self.response(json.dumps(rsp))
			return


		global TX_JSON_CACHE_PATH, MULTI_SIGN_THRESHOLD
		final_path = TX_JSON_CACHE_PATH + contract
		tx_json = self.read_from_file(final_path)
		multi_args = list(tx_json.get("multisig_configs", {}).keys())[0]

		sigs = tx_json.get("signatures", {})
		multi_sigs_list = sigs.get(multi_args, [])
		multi_sigs_len = len(multi_sigs_list)
		if multi_sigs_len == 0:
			sigs[multi_args] = [sig]
		elif multi_sigs_len < MULTI_SIGN_THRESHOLD:
			multi_sigs_list.append(sig)
			sigs[multi_args] = multi_sigs_list
		else:
			rsp = {"ret": -100, "msg": "the num of signers is satisfied"}
			self.response(json.dumps(rsp))
			return

		tx_json["signatures"] = sigs
		self.save_to_file(tx_json, final_path)
		name, msg = self.make_msg_for_lark(sig, args, digest, contract)
		title = "SIGN"
		tx_hash = ""
		if multi_sigs_len + 1 == MULTI_SIGN_THRESHOLD:
			ret, tx_hash = self.send_tx_file(final_path)
			if ret != 0:
				rsp = {"ret": -100, "msg": tx_hash}
				self.response(json.dumps(rsp))
				return
			else:
				pre_url = "https://explorer.nervos.org/transaction/"
				extra_msg = "\n=============\n" +\
					"the multi-signature has ended and the tx had been pushed to node(mac-mini), see: \n" +\
					pre_url + tx_hash
				msg = msg + extra_msg
				title = "END"
		elif multi_sigs_len == 0:
			fsize = os.path.getsize(final_path)
			extra_msg = "\n=============\n" +\
				name + " start a multi-sign transaction for contract:" +\
				contract + " size(" + str(fsize/1024.0) + " kb)"
			msg = msg + extra_msg
			title = "START"

		if comment != "":
			title = title + " (" + comment + ")"
		ret, msg = self.send_message(title, msg)

		rsp = {"ret": ret, "msg": msg}
		self.response(json.dumps(rsp))

		if title == "END":
			pid = os.fork()
			if pid == 0:
				self.wait_for_ready(tx_hash, contract)
				os.kill(os.getpid(), signal.SIGKILL)

		return

	def response(self, body):
		self.send_response(200)
		self.send_header('Content-Type', 'application/json')
		self.end_headers()
		self.wfile.write(body.encode())


	def send_message(self, title, text):
                robot_key = "284272ab-261b-4d67-800b-178cdb18e278"
		url = "https://open.larksuite.com/open-apis/bot/v2/hook/" + robot_key

		headers = {
			"Content-Type": "text/plain; charset=utf-8"
		}
		req_body = {
			"email": "xhxpecer@126.com",
			"msg_type": "post",
			"content": {
				"post": {
					"zh_cn": {
						"title": title,
						"content": [[{"tag": "text", "text": text}]]
					}
				}
			}
		}
		#print("text: " + text)
		data = json.dumps(req_body)

		try:
			response = requests.post(url=url, headers=headers, data=data)
		except requests.exceptions.RequestException:
			print('HTTP Request failed')
			return

		rsp_body = response.content
		rsp_dict = json.loads(rsp_body)
		code = rsp_dict.get("code", -100)
		msg = ""
		if code != 0:
			msg = "send message error, code = ", code, ", msg =", rsp_dict.get("msg", "")

		return code, msg

def run():
	port = 8000
	server_address = ('', port)
	httpd = HTTPServer(server_address, RequestHandler)
	print("start.....")
	httpd.serve_forever()

if __name__ == '__main__':
	run()
