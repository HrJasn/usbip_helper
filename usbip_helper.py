import argparse
import subprocess
import time
import requests
from flask import Flask, request, jsonify
import ssl

app = Flask(__name__)

def generate_cert():
    from OpenSSL import crypto
    from socket import gethostname
    from os.path import exists

    CERT_FILE = "cert.pem"
    KEY_FILE = "key.pem"

    if not exists(CERT_FILE) or not exists(KEY_FILE):
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 2048)

        cert = crypto.X509()
        cert.get_subject().C = "US"
        cert.get_subject().ST = "California"
        cert.get_subject().L = "San Francisco"
        cert.get_subject().O = "My Company"
        cert.get_subject().OU = "My Organization"
        cert.get_subject().CN = gethostname()
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha256')

        with open(CERT_FILE, "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        with open(KEY_FILE, "wt") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))

def parse_usbipd_list(output):
    lines = output.splitlines()
    shared_devices = []
    for line in lines:
        if "Shared" in line:
            parts = line.split()
            busid = parts[0]
            shared_devices.append(busid)
    return shared_devices


def sender_mode(interval, target, cert, key):
    previous_output = None
    while True:
        result = subprocess.run(['usbipd', 'list'], capture_output=True, text=True, encoding='utf-8', errors='ignore')
        output = result.stdout

        if output != previous_output:
            previous_output = output
            shared_devices = parse_usbipd_list(output)
            if shared_devices:
                busid = shared_devices[0]
                data = {'busid': busid}
                try:
                    if cert and key:
                        response = requests.post(target, json=data, cert=(cert, key), verify=False)
                    else:
                        response = requests.post(target, json=data)
                    print(f"Sent data: {data}, Response: {response.status_code}")
                except Exception as e:
                    print(f"Failed to send data: {e}")
        time.sleep(interval)

@app.route('/attach', methods=['POST'])
def attach_device():
    data = request.json
    busid = data['busid']
    ip = request.remote_addr
    try:
        result = subprocess.run(['sudo', 'usbip', 'attach', '--remote', ip, '--busid', busid], capture_output=True, text=True)
        return f"Attached {busid} from {ip}: {result.stdout}", 200
    except Exception as e:
        return f"Failed to attach {busid} from {ip}: {e}", 500

def receiver_mode(port, cert, key):
    if cert and key:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=cert, keyfile=key)
        app.run(host='0.0.0.0', port=port, ssl_context=context)
    else:
        app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='usbip helper script')
    parser.add_argument('--mode', choices=['sender', 'receiver', 'generate-cert'], required=True, help='Mode to run the script in')
    parser.add_argument('--interval', type=int, default=10, help='Interval in seconds for sender mode')
    parser.add_argument('--target', type=str, help='Target URL for sender mode')
    parser.add_argument('--port', type=int, default=8443, help='Port for receiver mode')
    parser.add_argument('--cert', type=str, help='Path to TLS certificate')
    parser.add_argument('--key', type=str, help='Path to TLS key')

    args = parser.parse_args()

    if args.mode == 'generate-cert':
        generate_cert()
    elif args.mode == 'sender':
        sender_mode(args.interval, args.target, args.cert, args.key)
    elif args.mode == 'receiver':
        receiver_mode(args.port, args.cert, args.key)
