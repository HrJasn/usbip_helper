
# usbip-helper

## 📦 專案簡介 / Project Description

`usbip-helper` 是一個輔助工具，基於以下專案實現：
- [linux/tools/usb/usbip](https://github.com/torvalds/linux/blob/master/tools/usb/usbip)
- [usbipd-win](https://github.com/dorssel/usbipd-win)

它利用 Flask 提供的接收端服務，或以 sender 模式（在 Windows 上）定期將可用 USB 裝置 busid 傳送到接收端，實現跨作業系統（Windows ↔ Linux）的 USB 設備共用。

This project is an auxiliary tool based on:
- [linux/tools/usb/usbip](https://github.com/torvalds/linux/blob/master/tools/usb/usbip)
- [usbipd-win](https://github.com/dorssel/usbipd-win)

It provides a Flask-based receiver service (Linux) or acts as a sender (Windows), periodically sending available USB device busids to the receiver, enabling USB device sharing across Windows and Linux.

---

## 🖥️ 支援平台 / Supported OS

✅ Linux  
✅ Windows（搭配 usbipd-win / with usbipd-win）

---

## ⚙️ 先決條件與安裝步驟 / Prerequisites & Installation (Ubuntu)

在 Ubuntu 上執行以下指令安裝所需套件：  
On Ubuntu, run the following commands to install required packages:

```bash
sudo apt update
sudo apt install -y usbip usbutils python3 python3-pip libssl-dev
sudo apt install -y python3-openssl python3-flask
pip3 install pyOpenSSL requests
```

---

## 🔧 核心模組掛載 / Kernel Modules (if not already built-in)

```bash
sudo modprobe vhci-hcd
sudo modprobe usbip-core
sudo modprobe usbip-host
```

---

## 🔑 產生 SSL 憑證（可選）/ Generate SSL Certificates (Optional)

```bash
python3 usbip_helper.py --mode generate-cert
```

此指令會在當前目錄中建立 \`cert.pem\` 與 \`key.pem\`。

---

## 🚀 運行模式 / Run Modes

### 1️⃣ Receiver（接收端 / Linux）

在接收端 Linux 執行以下指令：  
On the receiver (Linux):

```bash
python3 usbip_helper.py --mode receiver --port 8443 --cert cert.pem --key key.pem
```

此服務會監聽 HTTPS 連線，等待 Windows 發送可用的 busid 資料，並自動使用 \`usbip attach\` 掛載該裝置。

---

### 2️⃣ Sender（發送端 / Windows）

在 Windows（已安裝 usbipd-win）上執行以下指令（可在 WSL、Python 環境執行）：  
On the sender (Windows, with usbipd-win installed):

```bash
python3 usbip_helper.py --mode sender --target https://接收端IP:8443 --cert cert.pem --key key.pem --interval 10
```

此程式會每 10 秒執行一次 \`usbipd list\`，檢查當前共享的 USB 裝置，並將 busid 傳送給接收端。
