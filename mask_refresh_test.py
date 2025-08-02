#%%
from SLM_module import *
from pathlib import Path
import time

# instrument_carr_list = make_correction_and_zernike_arrays()

list_mask_paths = [
    Path(f'C:/Users/DELL/Desktop/SLM/SLM_X15213-02L/LCOS-SLM_USB_SLMControl/Test_sample_image_1272x1024/{str(i).zfill(3)}_1272x1024.bmp') for i in range(21)]
lst_uncorrected_masks = load_masks(list_mask_paths)
#%%
for mask in lst_uncorrected_masks:
    push_mask(mask)
    # time.sleep(0.02)
# %%
