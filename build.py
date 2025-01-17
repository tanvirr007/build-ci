import os
import subprocess
import requests
import re
import time
import psutil

# Configurações do Telegram
CHAT_ID = "SEU_CHAT_ID"
BOT_TOKEN = "SEU_BOT_TOKEN"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Configurações de build
LUNCH_TARGET = "aosp_spes-user"
BUILD_TARGET = "bacon"

# Funções para envio de mensagens ao Telegram
def send_telegram_message(message):
    try:
        url = f"{TELEGRAM_API_URL}/sendMessage"
        data = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data)
        return response.json().get("result", {}).get("message_id")
    except Exception as e:
        print(f"Erro ao enviar mensagem ao Telegram: {e}")

def edit_telegram_message(message_id, new_text):
    try:
        url = f"{TELEGRAM_API_URL}/editMessageText"
        data = {
            "chat_id": CHAT_ID,
            "message_id": message_id,
            "text": new_text,
            "parse_mode": "HTML",
        }
        requests.post(url, data=data)
    except Exception as e:
        print(f"Erro ao editar mensagem no Telegram: {e}")

def send_telegram_file(file_path, caption=""):
    try:
        url = f"{TELEGRAM_API_URL}/sendDocument"
        with open(file_path, "rb") as file:
            data = {"chat_id": CHAT_ID, "caption": caption}
            files = {"document": file}
            requests.post(url, data=data, files=files)
    except Exception as e:
        print(f"Erro ao enviar arquivo ao Telegram: {e}")

# Função para capturar informações do lunch
def get_lunch_info():
    try:
        process = subprocess.run(
            f"source build/envsetup.sh && lunch {LUNCH_TARGET}",
            shell=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
        )
        output = process.stdout
        rom_info = re.search(r"CUSTOM_VERSION=([\w\-.]+)", output)
        android_version = re.search(r"PLATFORM_VERSION=([\d.]+)", output)
        device = re.search(r"TARGET_PRODUCT=(\w+)", output)

        rom = rom_info.group(1) if rom_info else "Desconhecido"
        version = android_version.group(1) if android_version else "Desconhecido"
        device_name = device.group(1).split("_")[1] if device else "Desconhecido"

        return rom, version, device_name
    except Exception as e:
        print(f"Erro ao obter informações do lunch: {e}")
        return "Desconhecido", "Desconhecido", "Desconhecido"

def monitor_system_resources():
    try:
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return {
            "cpu": f"{cpu_usage}%",
            "ram": f"{memory.percent}%",
            "disk": f"{disk.used // (1024 ** 3)}GB/{disk.total // (1024 ** 3)}GB ({disk.percent}%)"
        }
    except Exception as e:
        print(f"Erro ao monitorar recursos do sistema: {e}")
        return {"cpu": "N/A", "ram": "N/A", "disk": "N/A"}


# Função para monitorar progresso do build
def monitor_build_progress(log_file, message_id, rom, version, device_name):
    progress_pattern = re.compile(r"\[\s*(\d+)%\s+(\d+/\d+)\s+([\d\w]+ remaining)\]")  # Captura progresso detalhado
    previous_progress = None
    try:
        with open(log_file, "r") as log:
            while True:
                line = log.readline()
                if not line:
                    time.sleep(1)
                    continue
                match = progress_pattern.search(line)
                if match:
                    percentage = match.group(1) + "%"  # Exemplo: "88%"
                    tasks = match.group(2)  # Exemplo: "104/118"
                    time_remaining = match.group(3)  # Exemplo: "5m49s remaining"
                    progress = f"{percentage} {tasks} {time_remaining}"
                    if progress != previous_progress:
                        # Monitorar recursos do sistema
                        resources = monitor_system_resources()
                        cpu = resources["cpu"]
                        ram = resources["ram"]
                        disk = resources["disk"]

                        # Atualizar mensagem no Telegram
                        new_text = (
                            f"🔄 <b>Compilando...</b>\n"
                            f"<b>ROM:</b> {rom}\n"
                            f"<b>Android:</b> {version}\n"
                            f"<b>Dispositivo:</b> {device_name}\n"
                            f"<b>Progresso:</b> {progress}\n"
                            f"<b>Recursos do Sistema:</b>\n"
                            f"• CPU: {cpu}\n"
                            f"• RAM: {ram}\n"
                            f"• Disco: {disk}"
                        )
                        edit_telegram_message(message_id, new_text)
                        previous_progress = progress
                if "ota_from_target_files.py - INFO    : done" in line:
                    break
    except Exception as e:
        print(f"Erro ao monitorar progresso: {e}")

# Função principal
def main():
    log_file = "build.log"
    try:
        # Capturar informações do lunch
        rom, version, device_name = get_lunch_info()

        # Enviar mensagem inicial e obter o ID da mensagem
        message_id = send_telegram_message(
            f"🟡 <b>Iniciando compilação...</b>\n"
            f"<b>ROM:</b> {rom}\n"
            f"<b>Android:</b> {version}\n"
            f"<b>Dispositivo:</b> {device_name}\n"
            f"<b>Progresso:</b> 0%"
        )

        # Criar o comando para configurar o ambiente e executar o build
        build_command = f"""
        source build/envsetup.sh && \
        lunch {LUNCH_TARGET} && \
        make {BUILD_TARGET} -j$(nproc)
        """

        # Iniciar o build e monitorar o progresso
        with open(log_file, "w") as log:
            build_process = subprocess.Popen(
                build_command,
                shell=True,
                executable="/bin/bash",
                stdout=log,
                stderr=log
            )

            # Monitorar progresso em paralelo
            monitor_build_progress(log_file, message_id, rom, version, device_name)

            # Aguardar conclusão do build
            build_process.wait()

        # Verificar resultado do build
        if build_process.returncode == 0:
            edit_telegram_message(
                message_id,
                f"🟢 <b>Compilação concluída com sucesso!</b>\n"
                f"<b>ROM:</b> {rom}\n"
                f"<b>Android:</b> {version}\n"
                f"<b>Dispositivo:</b> {device_name}",
            )
        else:
            edit_telegram_message(message_id, "🔴 <b>Compilação falhou!</b>")
            send_telegram_file(log_file, "🔴 <b>Log de erro:</b>")

    except Exception as e:
        send_telegram_message(f"🔴 <b>Erro inesperado:</b> {str(e)}")
    finally:
        if os.path.exists(log_file):
            send_telegram_file(log_file, "📄 <b>Log final:</b>")
            os.remove(log_file)

if __name__ == "__main__":
    main()
