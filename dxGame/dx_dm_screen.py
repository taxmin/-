import time

from dxGame import dxpyd


if __name__ == '__main__':
    from dxGame import DM
    import numpy as np,cv2
    from dxGame import MiniOpenCV
    dm = DM()
    dm.reg()
    dmc = DM_CAPTURE(dm)
    image = dmc.Capture()
    cv_image = np.asarray(image)
    cv2.imshow("image", cv_image)
    cv2.waitKey(0)
    # MiniOpenCV.imshow("image", image)
    # MiniOpenCV.waitKey(0)