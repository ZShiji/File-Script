import os
import re
import shutil
from datetime import datetime, timedelta


class Rename:
    def __init__(self):
        self.long_name = None
        self.short_name = None

    def process_folder(self, folder_path):
        """处理文件夹中的所有长文件"""
        target_folder = os.path.join(os.path.dirname(folder_path), "short")
        os.makedirs(target_folder, exist_ok=True)
        try:
            # 获取所有符合条件的文件
            long_files = [f for f in os.listdir(folder_path)
                          if len(f) > 30 and (
                f.endswith('.rnx') or       # RINEX文件
                'ORB.SP3' in f or          # 精密星历
                'CLK.CLK' in f or          # 精密钟差
                'OSB.BIA' in f or            # 相位偏差
                'ERP.ERP' in f            # 地球自转参数
            )]

            if not long_files:
                print(f"错误: 在{folder_path}中未找到长文件名格式文件")
                return False

            print(f"找到{len(long_files)}个长文件名格式文件")

            # 依次处理每个文件
            for long_file in long_files:
                print(f"\n正在处理: {long_file}")
                if long_file.endswith('.rnx'):
                    short_name = self.rinex_to_short(long_file)
                else:
                    short_name = self.product_to_short(long_file)
                if short_name:
                    # 复制并重命名文件
                    src_path = os.path.join(folder_path, long_file)
                    dst_path = os.path.join(target_folder, short_name)
                    shutil.copy2(src_path, dst_path)
                    print(f"已复制到: {dst_path}")

                # if long_file.endswith('.rnx'):
                #     self.convert_rinex(long_file)
                # elif 'ORB.SP3' in long_file:
                #     self.convert_sp3(long_file)
                # elif 'CLK.CLK' in long_file:
                #     self.convert_clk(long_file)
                # elif 'OSB.BIA' in long_file:
                #     self.convert_bias(long_file)

            return True

        except Exception as e:
            print(f"处理文件夹出错: {e}")
            return False

    def rinex_to_short(self, long_name):
        """rinex长文件名转短文件名
        例如: ABCD00XXX_R_20233330000_01D_30S_MO.rnx -> abcd3330.23o
        """
        try:
            # 解析长文件名
            station = long_name[:4]           # 测站名
            year = long_name[12:16]          # 年份
            doy = long_name[16:19]           # 年积日
            ext = long_name[-5].lower()  # 扩展名
            # 如果扩展名为n,则改为p
            if ext == 'n':
                ext = 'p'
            # 生成短文件名
            short_name = (f"{station.lower()}"   # 测站名小写
                          f"{doy}"                 # 年积日
                          f"0."                    # 会话标识
                          f"{str(year)[2:]}"    # 年份后两位
                          f"{ext}")                # 扩展名

            return short_name

        except Exception as e:
            print(f"文件名转换错误: {e}")
            return None

    def date_to_gps_week(self, year, doy):
        """计算GPS周和周内天"""
        date = datetime(year, 1, 1) + timedelta(days=doy-1)
        gps_epoch = datetime(1980, 1, 6)  # GPS起始时间
        days = (date - gps_epoch).days
        week = days // 7
        day = days % 7
        return week, day

    def product_to_short(self, long_name):
        """精密产品长文件名转短文件名
        例如: WUM0MGXRAP_20243020000_01D_05M_ORB.SP3 -> wum22223.sp3
        """
        try:
            # 解析长文件名
            agency = long_name[:3]          # 机构名(WUM)
            year = int(long_name[11:15])     # 年份
            doy = int(long_name[15:18])     # 年积日
            ext = long_name[-3:].lower()    # 扩展名(最后3个字符,小写)
            # 计算GPS周和周内天
            week, day = self.date_to_gps_week(year, doy)

            # 生成短文件名
            short_name = (f"{agency.lower()}"      # 机构名小写
                          f"{week:04d}"             # GPS周
                          f"{day}."                 # 周内天
                          f"{ext}")                   # 扩展名

            return short_name

        except Exception as e:
            print(f"产品文件名转换错误: {e}")
            return None


def main():
    renamer = Rename()
    # long_name = input("输入长文件名: ")
    folder = f"D:\PPPAR\MPPP-AR\products\HKCL0303\common"
    if os.path.exists(folder):
        renamer.process_folder(folder)
    else:
        print(f"错误: 目录{folder}不存在")
    # short_name = renamer.long_to_short(long_name)
    # if short_name:
    #     print(f"短文件名: {short_name}")


if __name__ == "__main__":
    main()
