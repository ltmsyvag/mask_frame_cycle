#%%
# demo 源于 https://github.com/basler/pypylon
from pypylon import pylon
import numpy as np
import numpy.typing as npt
def grab_frames(exposure_time: float, n_frames: int)->npt.NDArray[np.uint8]:
    """
    exposure_time 单位是微秒,
    返回 n 张图像的平均帧 (uint8)
    """
    camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
    camera.Open()
    camera.ExposureTime.Value = exposure_time  # set exposure time to 10 ms
    # print(camera.ExposureTime.Value)
    # for e in dir(camera):
    #     print(e)
    lst_frames = []
    numberOfFramesToGrab = n_frames
    camera.StartGrabbingMax(numberOfFramesToGrab)

    while camera.IsGrabbing():
        grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

        if grabResult.GrabSucceeded():
            frame = grabResult.Array
            lst_frames.append(frame)
        grabResult.Release()
    camera.Close()
    if len(lst_frames) == 1:
        return lst_frames[0]
    
    lst_frames = [img.astype(float) for img in lst_frames]
    avg_frame = sum(lst_frames) / len(lst_frames)
    avg_frame = np.round(avg_frame).astype(np.uint8)
    return avg_frame
#%%
# avg_img = grab_images(10000, 2)
# import matplotlib.pyplot as plt
# plt.imshow(avg_img, cmap='gray')
