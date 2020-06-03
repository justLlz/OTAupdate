# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)
#import webrepl
#webrepl.start()
import uos

class SystemCheck:
    """
    系统控制
    """

    def __init__(self):
        self.upgrade_directory = "upgrade"
        self.upgrade_file_list = set(["common.mpy", "config.json", "hmac.mpy", "main.py", "mqtt.mpy", "upgrade"
                                      "sha256.mpy", "urequestsd.mpy", "utils.mpy", "wifimgr.mpy", "sundry.mpy"])

    def copy_file(self, file):
        """
        复制文件./upgrade to ./
        """
        print("copy {}".format(file))
        if ".mpy" in file:
            with open("./{}/{}".format(self.upgrade_directory, file), "r") as f:
                with open("./{}".format(file), "wb") as w:
                    while True:
                        chunk = f.read(1024)
                        if chunk:
                            w.write(chunk)
                        else:
                            break
        else:
            with open("./{}/{}".format(self.upgrade_directory, file), "r") as f:
                with open("./{}".format(file), "w") as w:
                    w.write(f.read())
        w.close()
        f.close()

    def system_check(self):
        """
        upgrade_file_list: 云上需要下载的文件
        upgrade_dir_file_list: ./upgrade 目录下的文件
        original_file_list: ./ 工作目录下的文件
        """
        upgrade_dir_file_list = set(uos.listdir("./{}".format(self.upgrade_directory)))
        original_file_list = set(uos.listdir())
        if len(self.upgrade_file_list) <= len(upgrade_dir_file_list):  # 下载升级文件完成

            if original_file_list != upgrade_dir_file_list:  # 复制文件失败

                for upgrade_file in upgrade_dir_file_list:  # 重新复制

                    if upgrade_file != "upgrade":
                        
                        self.copy_file(upgrade_file)


if __name__ == "__main__":
    SystemCheck().system_check()