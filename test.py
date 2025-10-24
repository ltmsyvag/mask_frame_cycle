#%%
from PIL import Image
from core import push_nparray
import numpy as np
im = Image.open(r"Z:\设备说明书与软件\SLM\SLM_X15213-02L\Correction_patterns\CAL_LSH0905017_750nm.bmp")

arr = np.array(im)
push_nparray(arr)