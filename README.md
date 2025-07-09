为 105 写的 GS 自动迭代的仪器控制部分. 脚本流程:
1. 从 Z 盘取一张 `mask.bmp` (如果不存在, 则重复 check 直到 timeout 自动关闭)
2. 将 mask 和 correction, zernike 合并(用滨松提供的函数), 最后 apply lut. correction 和 lut 均有 780 和 813 两种波长选择
3. 将 `mask.bmp` 从 Z 盘上删除
4. 将合并的 mask 投屏到 SLM 上(滨松函数)
5. 用 balser 相机拍照, 得到 `frame.tif`
6. 将 `frame.tif` 上传到 Z 盘, 供 matlab 操作的 GS 算法脚本读取
7. 回到第一步

本 repo 中的文件:
- `LCOS-SLM_python_sample_01.py` :: 滨松 demo python 脚本. 其中有:
    - 相图计算函数(Fresnel lens, Laguerre-Gauss, Zernike, etc.)
    - `showOn2ndDisplay`. 比较重要的 SLM 投屏函数. 没什么意外的话, 相图的连续切换就是连续使用这个函数. 
    - `phaseSynthsizer`. 多相图合并
    - `makeBmpArray`. 没用, 貌似是把实际图像变为傅立叶相图的函数, 其中用到的 `Image_Tiling` 有点意思, 貌似是把任意大小的图像变换为 SLM 分辨率大小的图像
- `mask_frame_cycle.py` :: 实际使用的脚本, 改动自滨松 demo 脚本
- `Image_Control.h` :: 滨松 C runtime lib 的 header. 这是了解其 C runtime 功能的唯一来源. 其中有:
    - 计算相图(Fresnel lens, Laguerre-Gauss, Zernike, etc.)的 C 函数
    - SLM 屏幕选择以及参数设置 `Window_Settings`
    - SLM 投屏函数 `Window_Array_to_Display`
    - 以上两个函数都是 python 脚本 通过 ctypes 往 SLM 投屏相图所需的函数. 下一个 `Window_Term` 函数倒不是必要的
    - 关闭投屏窗口(一个占满整个屏幕的无 margin 窗口, 可以用 SLM 屏幕的全部像素显示相图). 我们的应用是连续变换相图, 因此用不着关闭这个窗口, 或者最后手动关闭即可. 
    - `Image_Tiling` 之前提到过
    - 其他对我们没啥用的函数. 
- `Image_Control.dll` 滨松 py 脚本所用的 C runtime
- `correction780.bmp`, `correction813.bmp` :: 滨松 SLMControl3.exe 导出的在两个不同波长下的 correction mask (无 LUT). 
- `pypylongrab.py` :: basler 拍照脚本, 用的是 basler 官方 python 相机控制包 pypylon