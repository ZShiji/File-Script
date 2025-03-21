
import os
import sys
from ftplib import FTP
import shutil
import gzip
import urllib.request
from datetime import datetime, timedelta


class PPPDownloader:
    def __init__(self):
        self.base_dir = "products"
        self.product_dir = None
        self.dirs = None
        self.ftp = None

    def process_folder(self, folder_path):
        """处理文件夹中的所有o文件"""
        try:
            # 获取所有.o文件
            o_files = [f for f in os.listdir(folder_path) if f.endswith(
                '.o') or f[-5].upper() == 'O']

            if not o_files:
                print(f"错误: 在{folder_path}中未找到.o文件")
                return False

            print(f"找到{len(o_files)}个观测文件")

            # 依次处理每个文件
            for obs_file in o_files:
                print(f"\n正在处理: {obs_file}")
                self.get_products(obs_file)

            return True

        except Exception as e:
            print(f"处理文件夹出错: {e}")
            return False

    def r(self, dir_name):
        """设置产品目录"""
        self.product_dir = os.path.join(self.base_dir, dir_name)
        self.dirs = {
            "common": os.path.join(self.product_dir, "common"),
            # "ion": os.path.join(self.product_dir, "ion"),
            "vmf": os.path.join(self.product_dir, "vmf")
        }

    def create_dirs(self):
        """创建必要的目录"""
        for dir_path in self.dirs.values():
            os.makedirs(dir_path, exist_ok=True)

    def download_ftp(self, url, save_path, retry_count=3):
        """FTP下载实现"""
        try:
            # 解析FTP URL
            host = url.split('/')[2]
            path = '/' + '/'.join(url.split('/')[3:])

            # 连接FTP服务器
            self.ftp = FTP(host)
            self.ftp.login()

            # 获取文件大小
            file_size = self.ftp.size(path)

            # 下载文件
            with open(save_path, 'wb') as f:
                def callback(data):
                    f.write(data)
                    progress = f.tell() / file_size * 100
                    sys.stdout.write(f"\r下载进度: {progress:.2f}%")
                    sys.stdout.flush()

                self.ftp.retrbinary(f'RETR {path}', callback)

            print(f"\n文件下载完成: {os.path.basename(save_path)}")
            return True

        except Exception as e:
            print(f"FTP下载错误: {e}")
            if retry_count > 0:
                print(f"正在重试,剩余{retry_count}次...")
                return self.download_ftp(url, save_path, retry_count-1)
            return False

        finally:
            if self.ftp:
                self.ftp.quit()

    def download_file(self, url, save_path):
        """统一下载接口"""
        try:
            # 判断URL类型
            if url.startswith('ftp://'):
                success = self.download_ftp(url, save_path)
            else:
                # 使用原有HTTP下载
                urllib.request.urlretrieve(url, save_path)
                success = True

            # 处理压缩文件
            if success and save_path.endswith(('.gz', '.Z')):
                with gzip.open(save_path, 'rb') as f_in:
                    with open(save_path[:-3], 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(save_path)

            return success

        except Exception as e:
            print(f"下载错误 {url}: {e}")
            return False

    def get_products(self, obs_file):
        """根据观测文件下载对应的产品"""
        # 从文件名解析日期
        if len(obs_file) == 12:  # 旧格式: ssss3330.23o
            year = 2000 + int(obs_file[9:11])
            doy = int(obs_file[4:7])
            dir_name = obs_file[:4]+obs_file[9:11]+obs_file[4:7]
        else:  # 新格式: SSSS00XXX_R_YYYYDDDHHMM
            year = int(obs_file[12:16])
            doy = int(obs_file[16:19])
            dir_name = obs_file[:4]+obs_file[12:16]+obs_file[16:19]
        self.r(dir_name)
        date = datetime(year, 1, 1) + timedelta(days=doy-1)

        # 保存日期信息
        self.year = date.year
        self.month = date.month
        self.day = date.day
        self.doy = doy
        # 构                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 建下载URL
        urls = {
            "sp31": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/orbit/WUM0MGXRAP_{year}{doy-1:03d}0000_01D_05M_ORB.SP3.gz",
            "sp32": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/orbit/WUM0MGXRAP_{year}{doy:03d}0000_01D_05M_ORB.SP3.gz",
            "sp33": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/orbit/WUM0MGXRAP_{year}{doy+1:03d}0000_01D_05M_ORB.SP3.gz",
            "clk": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/clock/WUM0MGXRAP_{year}{doy:03d}0000_01D_30S_CLK.CLK.gz",
            "erp": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/orbit/WUM0MGXRAP_{year}{doy:03d}0000_01D_01D_ERP.ERP.gz",
            "bia": f"ftp://igs.gnsswhu.cn/pub/whu/phasebias/{year}/bias/WUM0MGXRAP_{year}{doy:03d}0000_01D_01D_OSB.BIA.gz",
            "atx": "https://files.igs.org/pub/station/general/igs20.atx",
            "p": f"ftp://igs.gnsswhu.cn/pub/gps/data/daily/{year}/{doy:03d}/{str(year)[2:4]}p/BRDM00DLR_S_{year}{doy:03d}0000_01D_MN.rnx.gz",
            # ftp: // igs.gnsswhu.cn/pub/gps/products/2309 /
            # "ion": f"ftp://ftp.aiub.unibe.ch/CODE/{year}/CODG{doy:03d}0.{str(year)[2:]}I.Z",
        }

        # VMF URLs
        vmf_base = f"http://vmf.geo.tuwien.ac.at/trop_products/GRID/2.5x2/VMF1/VMF1_OP/{year}/"
        vmf_files = [
            f"VMFG_{year}{self.month:02d}{self.day:02d}.H{hour:02d}" for hour in range(0, 24, 6)]
        urls["vmf"] = [vmf_base + f for f in vmf_files]

        # 下载文件
        self.create_dirs()
        for product, url in urls.items():
            if isinstance(url, list):
                for u in url:
                    filename = os.path.basename(u)
                    save_path = os.path.join(self.dirs["vmf"], filename)
                    self.download_file(u, save_path)
            else:
                filename = os.path.basename(url)
                if product in ["sp31", "sp32", "sp33", "clk", "erp", "bia", "atx", "p"]:
                    save_path = os.path.join(self.dirs["common"], filename)
                elif product == "ion":
                    save_path = os.path.join(self.dirs["ion"], filename)
                self.download_file(url, save_path)


def main():
    downloader = PPPDownloader()
    # folder = tinpu("请输入观测文件目录路径: ")
    folder = f"D:/PPPAR/1"
    if os.path.exists(folder):
        downloader.process_folder(folder)
    else:
        print(f"错误: 目录{folder}不存在")


if __name__ == "__main__":
    main()
