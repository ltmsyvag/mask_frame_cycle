#%%
from SLM_module import *
from pathlib import Path
# instrument_carr_list = make_correction_and_zernike_arrays()
instrument_carr_list = []
list_mask_paths = [
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
    Path('Z:/实验数据/2025/7月/7.24/AI/相图结果/1_pred_phase.bmp'),
]
lst_carrs = [import_bmp_to_carr(path) for path in list_mask_paths]

for carr in lst_carrs:
    apply_mask(carr, instrument_carr_list=instrument_carr_list, use_lut=True)
# %%
