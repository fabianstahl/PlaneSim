import requests
import os
import tqdm
import numpy as np
import time
import configparser

from pathos.pools import ProcessPool
from PIL import Image, UnidentifiedImageError
from io import BytesIO

headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"}



def chunk_worker(x, y, z, root_dir, tile_url):
    file_path = os.path.join(root_dir, "{}/{}/{}.png".format(z, y, x))
    if os.path.exists(file_path):
        #print("WARNING: File Path '{}' already exists! Skipping ...".format(file_path))
        return
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    try:
        while(True):
            try:
                imgstr = requests.get(tile_url.format(z, x, y), headers=headers, timeout=5)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                print("WARNING! Timeout for '{}'! Trying again ...".format(file_path))
                continue
            except:
                raise

            # Server does not have image!
            try:
                tile = Image.open(BytesIO(imgstr.content))
            except UnidentifiedImageError:
                print("WARNING! The Server does not seem to have the tile '{}'! Skipping ...".format(file_path))
                return

            if tile.size == (256, 256):
                tile.save(file_path)
                if os.stat(file_path).st_size == 0:
                    print("WARNING! Download '{}' yielded empty image! Trying again ...".format(file_path))
                    continue
                return
            else:
                print("WARNING! Download '{}' did not yield correct image! Trying again ...".format(file_path))
                continue
    except:
        raise



def download_pyramid(configs, z_start=0, z_end=11, no_workers = 10):

    root_dir = configs.get("target_path")
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    no_tiles = np.sum([2**i * 2**i for i in range(z_start, z_end)])

    worker_args = []
    for z in range(z_start, z_end):
        for x in range(0, 2**z):
            for y in range(0, 2**z):
                worker_args.append((x, y, z, root_dir, configs.get("tile_url")))

    with ProcessPool(nodes = no_workers) as pool:
        results = pool.amap(chunk_worker, *zip(*worker_args))
        with tqdm.tqdm(total=len(worker_args)) as pbar:
            while not results.ready():
                no_files = sum([len(files) for r, d, files in os.walk(root_dir)])
                pbar.n = pbar.last_print_n = no_files
                pbar.refresh()
                time.sleep(5)
        results = results.get()



def summary(configs):

    for z in range(len(os.listdir(configs.get("target_path")))):
        lvl_dir     = os.path.join(configs.get("target_path"), str(z) + "/")
        files       = [os.path.join(dp, f) for dp, dn, filenames in os.walk(lvl_dir) for f in filenames]
        no_zeros    = len([f for f in files if os.stat(f).st_size == 0])
        print("""z-{}\t - images:\t{}\t, missing:\t{}, zero:\t{}""".format(z, len(files), (2**z * 2**z) - len(files), no_zeros))



def select_source(configs):
    
    valid_input = False
    while not valid_input:
        for i, section in enumerate(configs.sections()):
            print("{}:\t{}".format(i, section))
        inp = input("\nSelect a number: ")
        try:
            inp = int(inp)
            if inp < len(configs.sections()):
                return configs[configs.sections()[inp]]
        except:
            pass
        print("\nPlease enter a valid input!\n")

        

def select_max_z_level(min_lvl = 1, max_lvl = 11):

    valid_input = False
    while not valid_input:
        level = input("Select a maximum zoom level ({} - {}): ".format(min_lvl, max_lvl))
        try:
            level = int(level)
            if min_lvl <= level <= max_lvl:
                return level
        except:
            pass
        print("\nPlease enter a valid zoom level!\n")



def select_finished():
    
    done = input("Download more data? (0: No, 1: Yes) ")
    return done == "0"



if __name__ == "__main__":

    config = configparser.ConfigParser()
    config.read("crawler_configs.ini")

    done = False
    while not done:
        
        # Select a source configuration
        source_cfg  = select_source(config)

        # Select a maximum zoom level
        level       = select_max_z_level()

        # Download data
        download_pyramid(source_cfg, z_end = level)

        # print summary
        summary(source_cfg)

        # Download more?
        done = select_finished()
            