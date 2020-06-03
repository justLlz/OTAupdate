import uos
import os
import gc
import urequests
import ujson
import json
import machine
import network


class OTAUpdater:
    """
    OTA升级
    """

    def __init__(self):
        self.update_url = "http://update.huamod.com/mcu.json"
        self.file_url = "http://update.huamod.com/fils"
        self.file_path = "./upgrade/"
        self.boot_file = "boot.py"
        self.file_type = None
        self.download_error = False

    def check_version(self):
        pass

    def write_file(self, file_name, file_data, file_type=None):
        """
        写数据文件
        """
        if file_type == 'json':
            with open(self.file_path + file_name, 'w') as f:
                json.dump(file_data, f)
        else:
            with open(self.file_path + file_name, 'wb') as f:
                f.write(file_data)

    def copy_file(self, file):
        """
        复制文件./upgrade to ./
        """
        try:
            print("copy {}".format(file))
            if ".mpy" in file:
                with open(self.file_path + file, "r") as f:
                    with open("./{}".format(file), "wb") as w:
                        while True:
                            chunk = f.read(1024)
                            if chunk:
                                w.write(chunk)
                            else:
                                break
            else:
                with open(self.file_path + file, "r") as f:
                    with open("./{}".format(file), "w") as w:
                        w.write(f.read())
        except Exception as e:
            print("copy file:{} fail!{},{}".format(file, type(e).__name__, e))
        w.close()
        f.close()


    def download_update_list_update(self, file_list_url):
        """
        下载所有的代码文件!
        original_file_list: 本地文件列表
        down_file_list：需要升级的文件列表
        """
        version_index = urequests.get(file_list_url).json()
        latest_version = version_index["latest_version"]
        upgrade_file_list = version_index["version_list"][latest_version]
        version_flag = 'v' + latest_version.replace('.', '')
        file_name_url = {file_name: '{}/{}/{}'.format(
            self.file_url, version_flag, file_name) for file_name in upgrade_file_list}
        for file_name, file_url in file_name_url.items():
            self.download_update_files(file_name, file_url)
            if self.download_error:
                break
        return upgrade_file_list

    def download_update_files(self, file_name, file_url):
        """
        下载完成在本地改名为-new-xxx
        """
        print("Downloading:{}".format(file_name))
        try:
            response = urequests.get(file_url)
            if response.status_code == 200:
                if '.json' in file_name:
                    file_data = response.json()
                    if file_name == 'config.json':
                        # 如果是config.json直接更新
                        local_profiles = ConfigFileOp().read_config(1)
                        file_data["USER_CONF"] = local_profiles["USER_CONF"]
                        file_data["Ctrl_plan"] = local_profiles["Ctrl_plan"]
                        file_data["MQTT_CONF"] = local_profiles["MQTT_CONF"]
                        file_data["Electricity_times"] = local_profiles["Electricity_times"]
                elif '.mpy' in file_name:
                    file_data = response.content
                else:
                    file_data = response.text

                if '.json' in file_name:
                    self.file_type = "json"
                else:
                    self.file_type = None

                self.write_file(file_name, file_data, self.file_type)
            else:
                self.download_error = True
        except Exception as e:
            print("Downloading:{} fail!{},{}".format(file_name, type(e).__name__, e))
            self.download_error = True

        if response:
            response.close()
        gc.collect()

    def update_reset(self):
        """
        old_file_list：下载完成文件之后,将original_file改名为-old-,以便更新失败系统恢复
        """
        upgrade_file_list = self.download_update_list_update(self.update_url)
        if self.download_error:
            # 如果下载出现错误
            self.upgrade_restore()
        else:
            self.copy_file(self.boot_file)
            upgrade_file_list.remove(self.boot_file)
            for upgrade_file in upgrade_file_list:
                self.copy_file(upgrade_file)
            machine.reset()

    def upgrade_restore(self):
        print("system restore !!")
        for file in uos.listdir(self.file_path):
            uos.remove("{}{}".format(self.file_path, file))
        print("system restore end !!")

