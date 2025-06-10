TODO


# PlaneSim
PlaneSim is a fast-paced game where you race to deliver packages to international airports while navigating around storms and avoiding collisions with other aircraft.

# Setup
Clone repository and install dependencies (Note: a virtual environment is recommended)
```
    git clone git@github.com:fabianstahl/PlaneSim.git
    cd PlaneSim
    pip install -r requirements
```

Download xyz tiles and follow instructions. These tiles are needed as game textures and are free. Depending on the zoom level this might take a while. A minimum zoom level of 6 is recommended.
```
python download_tiles.py
```

You can now start the game
```
python app.py
```

# TODOs
* Add Tiling around world borders / seemless transitions
* Add Package Drop Of functionality
* Add Airplane Shadow
* Add other airplanes
* Add dangerous cloud crashes
* write README