#%%
# -*- coding: utf-8 -*-
"""
Created on Mon May 18 14:10:00 2020

@author: HPK
@edited: haiteng 2025
"""

from PIL import Image
import numpy as np
from ctypes import *
import copy
import time
from pathlib import Path
from pypylongrab import grab_frames
import tifffile


#LCOS pixel size
x = 1272
y = 1024

#pixel number
array_size = x * y
# make the 8bit unsigned integer array type
FARRAY = c_uint8 * array_size

def make_correction_and_zernike_arrays(wv_len: int):
    #pixelpitch(0: 20um 1: 12.5um)
    pitch = 1
    if wv_len == 780:
        carr_correction = import_bmp_to_carr("correction780.bmp")
    elif wv_len == 813:
        carr_correction = import_bmp_to_carr("correction813.bmp")
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
def load_mask(mask_path: Path, wv_len: int, carr_list: list):

    #LCOS-SML monitor number setting
    monitorNo = 2
    windowNo = 0
    xShift = 0
    yShift = 0
    carr_synth = FARRAY(0)
    carr_mask = import_bmp_to_carr(mask_path)
    phaseSynthesizer(
        [carr_mask]+carr_list
                    , carr_synth)
    apply_lut(wv_len, carr_synth)
    showOn2ndDisplay(monitorNo, windowNo, x, xShift, y, yShift, carr_synth)

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
    dict_wvlen_numwrap = {
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
def print_time_consumption(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken by {func.__name__}: {(end_time - start_time)*1e3:.2f} ms")
        return result
    return wrapper

def makeAxiconLensArray(top, pitch, x, y, array):
    '''
    the function for making AxiconLens pattern array
    double top: Top level of AxiconLens pattern. (/pi rad)
    int pitch: Pixel pitch. 0: 20um 1: 1.25um
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned integer array array: output array
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll") #for cdll
    Lcoslib = windll.LoadLibrary("./Image_Control.dll") #for windll
    AxiconLens = Lcoslib.AxiconLens
    AxiconLens.argtyes = [c_double, c_int, c_int, c_int, c_void_p, c_void_p]
    AxiconLens.restype = c_int
    if(pitch != 0 and pitch != 1):
        print("Error: AxiconLensFunction. invalid argument (pitch).")
        return -1
    # input argument to dll function.
    AxiconLens(c_double(top), pitch, x, y, byref(c_int(x*y)), byref(array))
    return 0

def makeCylindricalLensArray(forcus, wavelength, pitch, modeSelect, x, y, array):
    '''
    the function for making CylindricalLens pattern array
    int focus: the forcus of cylindrical lens. (mm)
    int wavelength: the wavelength of light. (nm)
    int pitch: Pixel pitch. 0: 20um 1: 1.25um
    int modeSelect: 0: horizontal or 1: vertical
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned int array array: output array
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    CylindricalLens = Lcoslib.CylindricalLens
    CylindricalLens.argtyes = [c_int, c_int, c_int, c_int, c_int, c_int, c_void_p, c_void_p]
    CylindricalLens.restype = c_int
    if(pitch != 0 and pitch != 1):
        print("Error: CylindricalLensFunction. invalid argument (pitch).")
        return -1
    CylindricalLens(forcus, wavelength, pitch, modeSelect, x, y, byref(c_int(x*y)), byref(array))
    return 0

def makeDiffractionPatternArray(rowOrColumn, gradiationNo, gradiationWidth, slipFactor, x, y, array):
    '''
    the function for making Diffraction pattern array
    int rowOrColumn: 0: horizontal or 1: vertical
    int gradiationNo: the number of gradiation.
    int gradiationWidth: the width of gradiation.
    int slipFactor: slip factor.
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned int array array: output array
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    Diffraction_pattern = Lcoslib.Diffraction_pattern
    Diffraction_pattern.argtyes = [c_int, c_int, c_int, c_int, c_int, c_int, c_void_p, c_void_p]
    Diffraction_pattern.restype = c_int
    Diffraction_pattern(rowOrColumn, gradiationNo, gradiationWidth, slipFactor, x, y, byref(c_int(x*y)), byref(array))
    return 0

def makeLaguerreGaussModeArray(p, m, pitch, beamSize, x, y, array):
    '''
    the function for making LaguerreGaussMode pattern array
    int p: radial index
    int m: azimuthal index 
    int pitch: Pixel pitch. 0: 20um 1: 1.25um
    double beamSize: Beam size (mm)
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned int array array: output array
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    LaguerreGaussMode = Lcoslib.LaguerreGaussMode
    LaguerreGaussMode.argtyes = [c_int, c_int, c_int, c_double, c_int, c_int, c_void_p, c_void_p]
    LaguerreGaussMode.restype = c_int
    if(pitch != 0 and pitch != 1):
        print("Error: LaguerreGaussModeFunction. invalid argument (pitch).")
        return -1
    LaguerreGaussMode(p, m, pitch, c_double(beamSize), x, y, byref(c_int(x*y)), byref(array))
    return 0

def makeFresnelLensArray(forcus, wavelength, pitch, x, y, array):
    '''
    the function for making FresnelLens pattern array
    int focus: the forcus of cylindrical lens. (mm)
    int wavelength: the wavelength of light. (nm)
    int pitch: Pixel pitch. 0: 20um 1: 1.25um
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned int array array: output array
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    FresnelLens = Lcoslib.FresnelLens
    FresnelLens.argtyes = [c_int, c_int, c_int, c_int, c_int, c_int, c_void_p, c_void_p]
    FresnelLens.restype = c_int
    if(pitch != 0 and pitch != 1):
        print("Error: FresnelLensFunction. invalid argument (pitch).")
        return -1
    FresnelLens(forcus, wavelength, pitch, x, y, byref(c_int(x*y)), byref(array))
    return 0
@print_time_consumption
def make_zernike_array(m, n, beam_diam_mm, coeff, pitch, x, y, array):
    '''
    haiteng 按照 c library header 文件做的 zernike mask 函数, hamamatsu 没有提供
    '''
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("./Image_Control.dll")
    Zernike = Lcoslib.Zernike
    Zernike.argtypes = [c_int, c_int, c_double, c_double, c_int, c_int, c_int, c_void_p, c_void_p]
    Zernike.restype = c_int
    Zernike(m, n, beam_diam_mm, coeff, pitch, x, y, byref(c_int(x*y)), byref(array))
    return 0

def makeBmpArray(filepath, x, y, outArray):
    '''
    the function for making FresnelLens pattern array
    String filepath: image file path.
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    8bit unsigned int array outArray: output array
    '''
    im = Image.open(filepath)
    imageHeight, imageWidth = im.size
    im_gray = im.convert("L")
    
    print("Imagesize = {} x {}".format(imageWidth, imageHeight))
    
    for i in range(imageWidth):
        for j in range(imageHeight):
            outArray[i+imageWidth*j] = im_gray.getpixel((i,j))
    
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    
    #Create CGH
    inArray = copy.deepcopy(outArray)
    Create_CGH_OC = Lcoslib.Create_CGH_OC
    Create_CGH_OC.argtyes = [c_void_p, c_int, c_int, c_int, c_int, c_void_p, c_void_p]
    Create_CGH_OC.restype = c_int
    
    repNo = 100
    progressBar = 1
    Create_CGH_OC(byref(inArray), repNo, progressBar, imageWidth, imageHeight, byref(c_int(imageHeight*imageWidth)), byref(outArray))
    
    #Tilling the image
    inArray = copy.deepcopy(outArray)
    Image_Tiling = Lcoslib.Image_Tiling
    Image_Tiling.argtyes = [c_void_p, c_int, c_int, c_int, c_int, c_int, c_void_p, c_void_p]
    Image_Tiling.restype = c_int
    
    Image_Tiling(byref(inArray), imageWidth, imageHeight, imageHeight*imageWidth, x, y, byref(c_int(x*y)), byref(outArray))
    
    return 0


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
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    
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
    
    # return 0

def imageRotation(inputArray, degree, x, y, outputArray):
    '''
    the function for Srotating image
    input 1D array inputArray: input array. 
    double degree: rotation degree (deg.)
    int x: Pixel number of x-dimension
    int y: Pixel number of y-dimension
    output 1D array outputArray: output array. 
    '''  
    #Lcoslib = cdll.LoadLibrary("Image_Control.dll")
    Lcoslib = windll.LoadLibrary("Image_Control.dll")
    
    Image_Rotation = Lcoslib.Image_Rotation
    Image_Rotation.argtyes = [c_void_p, c_double, c_int, c_int, c_void_p, c_void_p]
    Image_Rotation.restype = c_int
    Image_Rotation(byref(inputArray), c_double(degree), x, y, byref(c_int(x*y)), byref(outputArray))
    
    return 0

@print_time_consumption
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

timeout = 300 # seconds
check_interval = 1 # seconds
basler_exposure_time = 10 # microseconds
n_frames = 10
maskfile = Path("Z:/实验数据/2025/7月/7.8/自动化迭代相图/phase_input/mask.bmp")
framefile = Path("Z:/实验数据/2025/7月/7.8/自动化迭代相图/camera/frame.tif")


n_checks_max = timeout // check_interval
n_checks = n_checks_max
carr_list = make_correction_and_zernike_arrays(wv_len=813)
while n_checks:
    if maskfile.exists():
        load_mask(maskfile, wv_len=813, carr_list=carr_list)
        maskfile.unlink() # remove the file after loading
        avg_frame = grab_frames(basler_exposure_time, n_frames)
        tifffile.imwrite(framefile, avg_frame)
        n_checks = n_checks_max # top up n_checks
    else:
        time.sleep(check_interval)
        n_checks -= 1
        print(f'{n_checks} checks before timeout')
print('mask-frame cycle closed')
# %%
