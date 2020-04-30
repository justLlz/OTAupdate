import json
import urequests
import os
import uos
from utils import read_config, write_config

class OTAUpdater:
    """
    OTA升级
    """

    def __init__(self):
        self.update_url = "http://update.huamod.com/mcu.json"
        self.file_url = "http://update.huamod.com/fils"
        self.download_error = False

    def check_version(self):
        pass

    def download_update_list_update(self, file_list_url):
        """
        下载所有的代码文件!

        original_file_list: 本地文件列表
        down_file_list：需要升级的文件列表
        new_file_list：需要升级的文件列表，下载完成在本地改名为-new-xxx

        """
        original_file_list = uos.listdir()
        version_index = urequests.get(file_list_url)
        version_index = version_index.json()
        latest_version = version_index["latest_version"]
        down_file_list = version_index["version_list"][latest_version]
        version_flag = 'v' + latest_version.replace('.', '')
        file_name_url = {file_name: '{}/{}/{}'.format(self.file_url, version_flag, file_name) for file_name in down_file_list}
        new_file_list = []
        for file_name, file_url in file_name_url.items():
            try:
                response = self.download_update_files(file_name, file_url)
            except Exception as e:
                print("Downloading:{} fail!".format(file_name))
                self.download_error = True
            else:
                new_file_list.append('new' + file_name)
            finally:
                if response:
                    response.close()
                gc.collect()

            if self.download_error:
                break

        return down_file_list, original_file_list, new_file_list

    def download_update_files(self, file_name, file_url):
        """
        下载完成在本地改名为-new-xxx
        """
        print("Downloading:{}".format(file_name))
        response = urequests.get(file_url)
        if '.json' in file_name:
            update_profiles = response.json()
            if file_name == 'config.json':
                # 如果是config.json直接更新
                local_profiles = read_config()
                update_profiles["USER_CONF"] = local_profiles["USER_CONF"]
                update_profiles["Ctrl_plan"] = local_profiles["Ctrl_plan"]
                update_profiles["MQTT_CONF"] = local_profiles["MQTT_CONF"]
                update_profiles["Electricity_times"] = local_profiles["Electricity_times"]
                write_config(update_profiles)
            else:
                with open('-new-' + file_name, 'w') as f:
                    json.dump(update_profiles, f)
        elif '.mpy' in file_name:
            with open('-new-' + file_name, 'w') as f:
                f.write(response.content)
        else:
            with open('-new-' + file_name, 'w') as f:
                f.write(response.text)
        return response

    def update_reset(self): 
        """
        old_file_list：下载完成文件之后,将original_file改名为-old-,以便更新失败系统恢复
        """
        for file in os.listdir():
            if file.startswith('-old-'):
                uos.remove(file)

        down_file_list, original_file_list, new_file_list = self.download_update_list_update(self.update_url)
        # 如果下载出现错误，则系统恢复
        if self.download_error:
            self.system_restore()
        else:
            old_file_list = []
            for original_file_name in original_file_list:
                # 把老文件重命名 + '-old-',除了config.json
                # original_file >> old_file
                # original_file_list >> old_file_list
                if original_file_name != 'config.json':
                    print('Rename:', original_file_name)
                    old_file_name = '{}{}'.format('-old-', original_file_name)
                    uos.rename(original_file_name,  old_file_name)
                    old_file_list.append(old_file_name)


            for file in uos.listdir():
                if file.startswith('-new-'):
                    # 更新文件 -new-
                    uos.rename(file, file[5:])
                if file.startswith('-old-'):
                    # 删除文件 -old-
                    try:
                        uos.remove(file)
                    except Exception as e:
                        print('Delete {} fail!.'.format(file))
            # 重启
            reset()

    def system_restore(self):
        print("system restore")
        for file in uos.listdir():
            if file.startswith('-new-'):
                uos.remove(file)
