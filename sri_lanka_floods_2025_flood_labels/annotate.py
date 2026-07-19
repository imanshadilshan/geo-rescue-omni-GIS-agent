import cv2
import numpy as np
import glob, os, csv
from skimage.morphology import reconstruction, remove_small_objects, remove_small_holes, binary_closing, disk

SRC_DIR = "/home/claude/work"
MASK_DIR = "/home/claude/work/masks"
PREVIEW_DIR = "/home/claude/work/preview"
os.makedirs(MASK_DIR, exist_ok=True)
os.makedirs(PREVIEW_DIR, exist_ok=True)

def water_mask(img_bgr):
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV).astype(np.int32)
    H, S, V = hsv[...,0], hsv[...,1], hsv[...,2]
    b, g, r = img_bgr[...,0].astype(np.int32), img_bgr[...,1].astype(np.int32), img_bgr[...,2].astype(np.int32)

    # Confident clear/open water: blue-cyan-teal hue, real saturation, not too dark/bright
    confident = (H >= 75) & (H <= 135) & (S > 40) & (V > 35) & (V < 225)

    # Turbid / muddy flood water & waterlogged ground candidate:
    # grayish-brown-blue, low saturation, mid-low brightness, blue channel not much lower than red
    turbid = (S < 95) & (V > 55) & (V < 190) & (b >= r - 20) & (~confident)

    candidate = confident | turbid

    # Grow confident seeds through connected candidate region (limits turbid false-positives
    # to areas actually touching real water, e.g. excludes isolated gray rooftops/roads)
    seed = np.zeros_like(candidate, dtype=np.float64)
    seed[confident] = 1.0
    mask_img = candidate.astype(np.float64)
    grown = reconstruction(seed, mask_img, method='dilation') > 0.5

    # Cleanup: drop tiny speckles, fill tiny holes, light closing to smooth boundaries
    h, w = grown.shape
    min_obj = max(30, int(h * w * 0.00003))
    cleaned = remove_small_objects(grown, min_size=min_obj)
    cleaned = remove_small_holes(cleaned, area_threshold=min_obj)
    cleaned = binary_closing(cleaned, disk(2))
    return cleaned

files = sorted(glob.glob(os.path.join(SRC_DIR, "*.png")))
results = []
for f in files:
    name = os.path.basename(f)
    img = cv2.imread(f, cv2.IMREAD_COLOR)
    if img is None:
        print("FAILED TO READ", name)
        continue
    m = water_mask(img)
    frac = float(m.mean())
    mask_name = os.path.splitext(name)[0] + "_mask.png"
    cv2.imwrite(os.path.join(MASK_DIR, mask_name), (m.astype(np.uint8) * 255))
    results.append((name, mask_name, frac))
    print(f"{name}: flood_fraction={frac:.4f}")

with open("/home/claude/work/mask_manifest.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["file", "mask_path", "flood_fraction"])
    for row in results:
        w.writerow(row)

print("DONE", len(results), "tiles processed")
