# 3D image tagger

This tool can import 3d point-clouds / camera poses / pictures and tag them:

- imports from MVE scenes
- renders point-cloud and cameras in 3d using opengl
- generates/refines point-cloud selections by hand (spherical selections)
- reprojects/exports point-cloud and selections into images (masks)

This code was developed in the scope of a research project:

[Deep-Learning Image Segmentation - Towards Tea Leaves Harvesting by Automomous Machine](https://sitehepia.hesge.ch/diplome/ITI/2018/ITI_MAT_soir_memoire_diplome_Ducommun_Dit_Boudry_Upegui_2018.pdf)

## Prerequisites

- Python 3.x
- QT Pyside2 >= 5.11
- OpenGL >= 2
- Precomputed MVE scenes

## How to run

```
python3 app.py
```

## License

GPLv3
