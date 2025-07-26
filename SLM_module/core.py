#%%
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 14:10:00 2020

@author: HPK (original file `LCOS-SLM_python_sample_01.py`)
@edited: haiteng 2025
"""
import os
from PIL import Image
import numpy as np
from ctypes import *
import time
from pathlib import Path
# from pypylongrab import grab_frames
# import tifffile

#LCOS pixel size
x = 1272
y = 1024

#pixel number
array_size = x * y
# make the 8bit unsigned integer array type
FARRAY = c_uint8 * array_size
# dll_path_abs = r"C:\Users\Tweezer Lab\OneDrive\Desktop\mask_frame_cycle\SLM_module\Image_Control.dll" # 出于奇怪的原因， 必须用 dll 的绝对路径才能在 dashboard 中不报错
script_dir = os.path.dirname(os.path.abspath(__file__))
dll_path_abs = script_dir+ r"\Image_Control.dll" # 出于奇怪的原因， 必须用 dll 的绝对路径才能在 dashboard 中不报错

def print_time_consumption(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken by {func.__name__}: {(end_time - start_time)*1e3:.2f} ms")
        return result
    return wrapper

def make_correction_and_zernike_arrays(wv_len: int=813)->list: # return a list of the strange FARRAY type
    """
    将 SLMControl3.exe 生成的 correction mask 和 Zernike masks (很多个) 放在一个列表中返回
    """
    #pixelpitch(0: 20um 1: 12.5um)
    pitch = 1
    if wv_len == 780:
        carr_correction = import_bmp_to_carr(script_dir + r'\correction780.bmp')
    elif wv_len == 813:
        carr_correction = import_bmp_to_carr(script_dir + r'\correction813.bmp')
    else:
        raise ValueError(f"Unsupported wavelength: {wv_len}")
    
    beam_diam_mm = 14.0
    znk_arr_list = []
    nmcoeff_list = [
        (2,0,-0.55),
        (2,-2,0.3),
        (2,2,0.3),
        (3,-3,0.1),
        (3,3,0.1),
        (4,0,-0.2),
        (4,-4,-0.3),
        (4,4,0.8),
        ]
    for n,m,coeff in nmcoeff_list:
        carr = FARRAY(0)
        make_zernike_array(m, n, beam_diam_mm, coeff, pitch, x, y, carr)
        znk_arr_list.append(carr)
    return [carr_correction]+znk_arr_list 

def load_mask_(mask_path: Path, wv_len: int, instrument_carr_list: list)->None:
    """
    读取用户的 mask 文件, 
    和 make_correction_and_zernike_arrays 提供的 SLM 仪器 mask 合成一个 mask (简单的 255 wrapping), 
    最后乘以 SLMControl.exe 显示的 LUT 因子 (round 后再取为 uint8)
    将结果投屏 SLM
    """
    #LCOS-SML monitor number setting
    monitorNo = 2
    windowNo = 0
    xShift = 0
    yShift = 0
    carr_synth = FARRAY(0)
    carr_mask = import_bmp_to_carr(mask_path)
    phaseSynthesizer(
        [carr_mask]+instrument_carr_list
                    , carr_synth)
    apply_lut(wv_len, carr_synth)
    showOn2ndDisplay(monitorNo, windowNo, x, xShift, y, yShift, carr_synth)

#LCOS-SML monitor number setting
monitorNo = 2
windowNo = 0
xShift = 0
yShift = 0
@print_time_consumption
def push_mask(carr_mask)->None:
    showOn2ndDisplay(monitorNo, windowNo, x, xShift, y, yShift, carr_mask)



def import_bmp_to_carr(filepath):
    """
    将 uint8 BMP 文件导入为 1d C 数组
    """
    im = Image.open(filepath)
    arr = np.array(im).flatten()
    CARR = c_uint8 * len(arr)
    carr = CARR(0)
    for i in range(len(arr)):
        carr[i] = c_uint8(arr[i])
    return carr

def apply_lut(laser_wvlen, carr):
    dict_wvlen_numwrap = { # 下面的两个 2π wrap 对应的像素值来源于滨松 GUI, SLMcontrol3.exe 
        780 : 205,
        813 : 214,
    }
    if laser_wvlen not in dict_wvlen_numwrap:
        raise ValueError(f"Unsupported wavelength: {laser_wvlen}")
    num_wrap = dict_wvlen_numwrap[laser_wvlen]
    arr = np.array(carr)
    arr = (np.round(arr * (num_wrap / 255))).astype(np.uint8)
    for i in range(len(arr)):
        carr[i] = c_uint8(arr[i])



@print_time_consumption
def make_zernike_array(m, n, beam_diam_mm, coeff, pitch, x, y, array):
    '''
    haiteng 按照 Image_Control.h 文件做的 zernike mask 函数, hamamatsu 没有提供
    '''
    Lcoslib = windll.LoadLibrary(dll_path_abs)
    Zernike = Lcoslib.Zernike
    Zernike.argtypes = [c_int, c_int, c_double, c_double, c_int, c_int, c_int, c_void_p, c_void_p]
    Zernike.restype = c_int
    Zernike(m, n, beam_diam_mm, coeff, pitch, x, y, byref(c_int(x*y)), byref(array))
    return 0

Lcoslib = windll.LoadLibrary(dll_path_abs)

#Select LCOS window
Window_Settings = Lcoslib.Window_Settings
Window_Settings.argtypes = [c_int, c_int, c_int, c_int]
Window_Settings.restype = c_int
Window_Settings(monitorNo, windowNo, xShift, yShift)

#Show pattern
Window_Array_to_Display = Lcoslib.Window_Array_to_Display
Window_Array_to_Display.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
Window_Array_to_Display.restype = c_int
# @print_time_consumption
def showOn2ndDisplay(monitorNo, windowNo, x, xShift, y, yShift, array):
    '''
    the function for showing on LCOS display
    int monitorNo: 
    int windowNo:
    int x: Pixel number of x-dimension
    int xShift: shift pixels of x-dimension
    int y: Pixel number of y-dimension
    int yShift: shift pixels of y-dimension
    8bit unsigned int array array: output array
    '''
    beg = time.time()
    Window_Array_to_Display(array, x, y, windowNo, x*y)
    end = time.time()
    print(f"Time taken to display: {(end - beg)*1e3:.2f} ms")
def showOn2ndDisplay_(monitorNo, windowNo, x, xShift, y, yShift, array):
    '''
    the function for showing on LCOS display
    int monitorNo: 
    int windowNo:
    int x: Pixel number of x-dimension
    int xShift: shift pixels of x-dimension
    int y: Pixel number of y-dimension
    int yShift: shift pixels of y-dimension
    8bit unsigned int array array: output array
    '''
    Lcoslib = windll.LoadLibrary(dll_path_abs)
    
    #Select LCOS window
    Window_Settings = Lcoslib.Window_Settings
    Window_Settings.argtypes = [c_int, c_int, c_int, c_int]
    Window_Settings.restype = c_int
    Window_Settings(monitorNo, windowNo, xShift, yShift)
    
    #Show pattern
    Window_Array_to_Display = Lcoslib.Window_Array_to_Display
    Window_Array_to_Display.argtypes = [c_void_p, c_int, c_int, c_int, c_int]
    Window_Array_to_Display.restype = c_int
    beg = time.time()
    Window_Array_to_Display(array, x, y, windowNo, x*y)
    end = time.time()
    print(f"Time taken to display: {(end - beg)*1e3:.2f} ms")
    #wait until enter key input
    # input("please input enter key...")
    # time.sleep(1)
    
    # #close the window
    # Window_Term = Lcoslib.Window_Term
    # Window_Term.argtyes = [c_int]
    # Window_Term.restype = c_int
    # Window_Term(windowNo)


# @print_time_consumption
def phaseSynthesizer(inputPatterns, outputArray):
    '''
    the function for Synthesizing image pattaerns
    input arrays 2D array inputPatterns: the compornents will be synthesized.
    output 1D array outputArray: output array. 
    '''  
    n = len(inputPatterns[0])
    outputPattern = np.zeros(n, dtype=int)
    for pattern in inputPatterns:
        outputPattern = outputPattern + pattern
    
    for i in range(n):
        outputArray[i] = c_uint8(outputPattern[i] % 256)    
    
    return 0

def load_and_correct_masks(list_mask_paths: list)->list:
    lst_correction_carrs = make_correction_and_zernike_arrays()

    lst_uncorrected_carrs = []
    for i, path in enumerate(list_mask_paths):
        lst_uncorrected_carrs.append(import_bmp_to_carr(path))
        print(f'mask {i} converted')
    lst_corrected_carrs = []
    for i, this_carr in enumerate(lst_uncorrected_carrs):
        carr_synth = FARRAY(0)
        phaseSynthesizer([this_carr]+lst_correction_carrs, carr_synth)
        lst_corrected_carrs.append(carr_synth)
        print(f'mask {i} corrected')
    return lst_corrected_carrs



# %%
