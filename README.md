# NDVI-vs-SAVI-Analysis


Objective
Comparative analysis of NDVI and SAVI over the project boundary, focused on vegetation response, soil background effects, saturation, and interpretation of pixel-level values.
1. Data & Methodology
AOI: Project Area.kml boundary, ~59.66 ha
Imagery: Sentinel-2 Level-2A Surface Reflectance (COPERNICUS/S2_SR_HARMONIZED)
Scene selection: filtered to Feb 2026, CLOUDY_PIXEL_PERCENTAGE < 40, sorted ascending, least-cloudy scene selected automatically
Selected scene: S2C_MSIL2A_20260215T053921_N0512_R005_T42QYM_20260215T085810 — 15 Feb 2026, cloud cover 0.001% (effectively cloud-free)
Cloud masking: QA60 bitmask (bits 10/11); bands scaled to 0–1 reflectance (÷10000)
Resolution / CRS: locked to native 10 m, EPSG:32642 (UTM Zone 42N) — correct zone for ~71.8°E
NDVI = (NIR − Red) / (NIR + Red)
SAVI = [(NIR − Red) / (NIR + Red + L)] × (1 + L), L = 0.5 (Huete, 1988 — mid-range value for moderate vegetation cover)
Both indices clipped to the project boundary, computed on an identical grid/CRS/extent for pixel-level alignment


GEE App link : https://ee2-iirs04nidhi.projects.earthengine.app/view/ndvi-and-savi-analysis     (it takes 30 - 60 sec. To open)
GEE Get Link : https://code.earthengine.google.com/5adc9597ed303aee64b1046769a0b54c

True Color: https://earthengine.googleapis.com/v1/projects/ee-iirs04nidhi/thumbnails/adc73403369f1e3391b9f10abfe7dfe0-ad857d8a85b327ba3155aa9af1d180c5:getPixels
NDVI:
https://earthengine.googleapis.com/v1/projects/ee-iirs04nidhi/thumbnails/9b2b77ad837d48c5d204645682d67d24-a072f5d6736b3c8174bc6a3e37931907:getPixels
SAVI:
https://earthengine.googleapis.com/v1/projects/ee-iirs04nidhi/thumbnails/c13445d35d494c53146452e2436358b5-58326f89df39fa4baaef48cb9b9ac6a6:getPixels

