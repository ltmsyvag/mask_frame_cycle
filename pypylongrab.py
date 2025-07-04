#%%
# demo 源于 https://github.com/basler/pypylon
from pypylon import pylon

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# demonstrate some feature access
new_width = camera.Width.Value - camera.Width.Inc
print(camera.Width.Value, camera.Width.Min, camera.Width.Max, camera.Width.Inc)
print(camera.ExposureTime.Value)
if new_width >= camera.Width.Min:
    camera.Width.Value = new_width
for e in dir(camera):
    print(e)
numberOfImagesToGrab = 1
camera.StartGrabbingMax(numberOfImagesToGrab)

while camera.IsGrabbing():
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

    if grabResult.GrabSucceeded():
        # Access the image data.
        print("SizeX: ", grabResult.Width)
        print("SizeY: ", grabResult.Height)
        img = grabResult.Array
        print("Gray value of first pixel: ", img[0, 0])

    grabResult.Release()
camera.Close()
#%%
import matplotlib.pyplot as plt
plt.imshow(img, cmap='gray')
# %%
