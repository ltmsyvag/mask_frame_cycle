#%%
from SLM_module import *
from pathlib import Path
import time

# instrument_carr_list = make_correction_and_zernike_arrays()

list_mask_paths = [
    Path(f'Z:/实验数据/2025/7月/7.24/AI/相图结果2/{num}_pred_phase.bmp') 
    for num in range(1,3+1)
]
lst_corrected_masks = load_and_correct_masks(list_mask_paths)
for mask in lst_corrected_masks:
    push_mask(mask)
    time.sleep(0.50)