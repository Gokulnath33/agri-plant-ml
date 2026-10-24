"""
download_crop_images.py
=======================
Downloads crop leaf images for empty dataset folders using Bing Image Crawler.
Run once to populate the dataset, then re-run train.py.
"""

import os
import time
from icrawler.builtin import BingImageCrawler

DATASET_DIR = "dataset"
IMAGES_PER_CLASS = 150

CROP_SEARCH_QUERIES = {
    "Apple":              "apple leaf healthy plant",
    "Arecanut":           "arecanut areca palm leaf plant",
    "Bamboo":             "bamboo leaf plant green",
    "Banana":             "banana leaf plant healthy",
    "Black_Pepper":       "black pepper plant leaf",
    "Buckwheat":          "buckwheat crop plant leaf",
    "Cardamom":           "cardamom plant leaf green",
    "Cashew":             "cashew plant leaf healthy",
    "Castor":             "castor plant leaf ricinus",
    "Chickpea":           "chickpea plant leaf crop",
    "Chilli":             "chilli pepper plant leaf",
    "Coconut":            "coconut palm leaf plant",
    "Coffee":             "coffee plant leaf green",
    "Coriander":          "coriander plant leaf herb",
    "Cotton":             "cotton plant leaf crop",
    "Cumin":              "cumin plant leaf herb",
    "Fruits":             "fruit plant leaf healthy",
    "Ginger":             "ginger plant leaf crop",
    "Grapes":             "grape vine leaf healthy",
    "Green_Gram":         "green gram mung bean plant leaf",
    "Groundnut":          "groundnut peanut plant leaf",
    "Jute":               "jute plant leaf crop",
    "King_Chilli":        "king chilli bhut jolokia plant leaf",
    "Lakadong_Turmeric":  "turmeric plant leaf lakadong",
    "Litchi":             "litchi lychee plant leaf",
    "Maize":              "maize corn plant leaf healthy",
    "Mango":              "mango plant leaf healthy",
    "Mustard":            "mustard plant leaf crop",
    "Oilseeds":           "oilseed crop plant leaf",
    "Onion":              "onion plant leaf crop",
    "Orange":             "orange citrus plant leaf",
    "Paddy":              "paddy rice plant leaf healthy",
    "Paddy_(Basmati)":    "basmati rice paddy plant leaf",
    "Pearl_Millet_(Bajra)": "pearl millet bajra plant leaf",
    "Pigeon_Pea":         "pigeon pea tur dal plant leaf",
    "Pineapple":          "pineapple plant leaf",
    "Potato":             "potato plant leaf healthy",
    "Pulses":             "pulses legume plant leaf",
    "Ragi":               "ragi finger millet plant leaf",
    "Rubber":             "rubber plant leaf hevea",
    "Soybean":            "soybean plant leaf healthy",
    "Sugarcane":          "sugarcane plant leaf",
    "Sunflower":          "sunflower plant leaf",
    "Tea":                "tea plant leaf camellia sinensis",
    "Tobacco":            "tobacco plant leaf",
    "Turmeric":           "turmeric plant leaf curcuma",
    "Vegetables":         "vegetable plant leaf healthy",
    "Wheat":              "wheat plant leaf crop",
}

def count_images(folder_path):
    valid = ('.jpg', '.jpeg', '.png', '.bmp')
    return len([f for f in os.listdir(folder_path) if f.lower().endswith(valid)])

def download_for_folder(folder_name, query, target_dir, num_images):
    os.makedirs(target_dir, exist_ok=True)
    existing = count_images(target_dir)
    if existing >= num_images:
        print(f"  [SKIP] {folder_name} already has {existing} images.")
        return existing
    print(f"  [DOWNLOAD] {folder_name}: searching '{query}'")
    try:
        crawler = BingImageCrawler(
            downloader_threads=4,
            storage={"root_dir": target_dir}
        )
        crawler.crawl(
            keyword=query,
            max_num=num_images,
            min_size=(100, 100),
            file_idx_offset=existing,
        )
    except Exception as e:
        print(f"  [ERROR] {folder_name}: {e}")
    after = count_images(target_dir)
    print(f"  [DONE] {folder_name}: {after - existing} downloaded ({after} total)")
    return after

def main():
    print("=" * 60)
    print("Crop Image Downloader")
    print("=" * 60)
    valid_exts = ('.jpg', '.jpeg', '.png', '.bmp')
    to_download = []
    for folder in sorted(os.listdir(DATASET_DIR)):
        fpath = os.path.join(DATASET_DIR, folder)
        if not os.path.isdir(fpath):
            continue
        imgs = [f for f in os.listdir(fpath) if f.lower().endswith(valid_exts)]
        if len(imgs) < 10 and folder in CROP_SEARCH_QUERIES:
            to_download.append(folder)
    print(f"Folders to populate: {len(to_download)}\n")
    for i, folder in enumerate(to_download, 1):
        query = CROP_SEARCH_QUERIES[folder]
        target = os.path.join(DATASET_DIR, folder)
        print(f"[{i}/{len(to_download)}] {folder}")
        download_for_folder(folder, query, target, IMAGES_PER_CLASS)
        time.sleep(1)
    print("\n" + "=" * 60)
    print("Download complete! Now run: python train.py")
    print("=" * 60)

if __name__ == "__main__":
    main()
