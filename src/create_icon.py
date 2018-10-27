#coding:utf-8
# 检查所有图片，生成xcode的icon
# @author xmf
# @date 2018.10.22
from PIL import Image
import sys
import threading
import os
import shutil
import time
import json

#_outFiles 	= {} 				#输出的文件
_isError 	= False 			#错误标志
_sTime 		= time.time()
_findFiles	= 0
_allFiles 	= []
_successNum = 0
_flag		= 0
_threadNum 	= 0
_hasAlpha0 	= False

#所有需要的尺寸
_pngSizes 	= [20, 29, 40, 50, 57, 58, 60, 72, 76, 80, 87, 100, 114, 120, 144, 152, 167, 180, 1024 ]				
_existSizes = {}
_configJson = {}

# 主函数
def main():
	print("\n==============start=============")
	args = sys.argv
	if len(args) <= 1:
		print("error: 没有输入根目录！！！")
		return

	_rootDir = args[1]
	print("开始遍历目录：", _rootDir)
	#查找所有图片文件
	#_rootDir = _rootDir.replace('\\', '/')
	print("_rootDir:",_rootDir)
	find_dir(_rootDir)
	time.sleep(0.1)
	while _isError == False and _successNum < len(_allFiles):
		showAndDoFile()
		time.sleep(0.01)

	#显示缺少size	
	isLackFile = False
	if _isError == False :
		for size in _pngSizes:
			if (size in _existSizes) == False:
				print("缺少的尺寸：", str(size) + "x" + str(size))
				isLackFile = True

		if _hasAlpha0 == False and isLackFile and (1024 in _existSizes):
			#转换尺寸
			op = input("是否要生成缺少的尺寸？y/n :")
			if str(op) != "y":
				return

	if _isError or _hasAlpha0:
		return

	showAndDoFile()
	print("\n")
	#检查配置文件
	jsonPath = os.getcwd() + "/config/icon.json"
	if os.path.exists(jsonPath) == False:
		print("\nerror 缺少配置文件 ", jsonPath)
		return

	with open(jsonPath, "r") as f:
		global _configJson
		_configJson = json.load(f)
		

	#输出图片目录
	outputFile(isLackFile)

	print("\n==============完成=============")



# 递归遍历当前目录
def find_dir(curr_path):
	files = os.listdir(curr_path)		# 获取当前目录下的所有文件及目录 
	global _sTime
	global _findFiles
	for file in files:					# 拿到的file是一个文件名
		file_path = os.path.join(curr_path, file)
		# print(">>> {0}".format(file_path))
		if os.path.isdir(file_path):
			if file == ".svn":
				continue

			find_dir(file_path)			# 进入目录递归
		else:
			(shotName, extension) = os.path.splitext(file)
			if extension == ".png":
				_allFiles.append(file_path)
			_findFiles += 1


# 显示遍历数量
def showAndDoFile():
	fileNum = len(_allFiles)
	global _flag
	_flag += 1
	global _threadNum	
	global _findFiles
	print("查找文件：", _findFiles, "目标文件数量：", fileNum, "进度:", _successNum, "/", fileNum,
		5*" ", (_flag % 5) * ".", "\r", end="")
	if _threadNum >= len(_allFiles):
		return

	encodePath = _allFiles[_threadNum]		# 找出当前要处理的文件
	if threading.activeCount() <= 8 and _threadNum < len(_allFiles):
		thread = PngThread(_threadNum, "Thread" + str(_threadNum))
		_threadNum += 1 				# 标记自增	
		thread.start()

#输出图片目录
def outputFile(isLackFile):
	outFolder = "AppIcon.appiconset"
	if os.path.exists(outFolder):
		files = os.listdir(outFolder)
		if len(files) > 0 :
			print("\nerror 请删除目录： ", outFolder)
			return
	else:
		os.makedirs(outFolder)  		# 创建目录

	for size in _pngSizes:
		nFilePath = outFolder + "/" + str(size) + "x" + str(size) + ".png"
		if (size in _existSizes) :			
			shutil.copy(_existSizes[size], nFilePath)
			print("copy:", nFilePath)
		elif isLackFile:
			im = Image.open(_existSizes[1024])
			resizeIm = im.resize((size, size), Image.ANTIALIAS)
			resizeIm.save(nFilePath)
			_existSizes[size] = nFilePath
			print("copy:", nFilePath)

	for item in _configJson["images"]:
		#print("size:", item["size"])
		w = float(item["size"].split("x")[0])
		if item["scale"] == "2x":
			w = w * 2
		elif item["scale"] == "3x":
			w = w * 3
		sw = int(w)
		if (size in _existSizes) == False:	
			print("警告：json表存在未知尺寸，", sw)

		item["filename"] = str(sw)+"x"+str(sw)+".png"

	#print("\njson：\n", _configJson)
	with open(outFolder + '/Contents.json', 'w') as f:
		json.dump( _configJson, f, indent = 4)

#使用继承threading的类来生成
class PngThread(threading.Thread):
	def __init__(self, threadID, name):
		threading.Thread.__init__(self)		#线程ID
		self.threadID = threadID
		self.name = name

	def run(self):
		path = _allFiles[self.threadID]
		try:
			im = Image.open(path)
			(x, y) = im.size;
			global _existSizes
			if (x in _existSizes) == False:
				_existSizes[x] = path
				self.checkPngAlpha(im, path)
		except BaseException:
			global _isError 
			_isError = True
			print(path + " 文件读取出错！")
		
		global _successNum
		_successNum += 1

	def checkPngAlpha(self, im, path):
		try:
			isAlpha0 = False
			datas = im.getdata()
			for px in datas:
				if len(px) == 4 and px[3] <= 0:					
					isAlpha0 = True
					break

			if isAlpha0 == True:
				global _hasAlpha0
				_hasAlpha0 = True
				print("error 存在透明图片：", path)
		except BaseException:
			global _isError 
			_isError = True
			print("error " + path + "文件解析出错！")
		

if __name__ == "__main__":
	main()

