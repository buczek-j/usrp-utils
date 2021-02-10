# usrp-utils

## GNU-Radio and UHD Python3 install 
Install instructions were taken from from [here](https://github.com/gnuradio/pybombs#pybombs)
```
sudo apt-get install python3-pip
sudo pip3 install pybombs
pybombs auto-config
pybombs recipes add-defaults
pybombs prefix init ~/prefix-3.8 -R gnuradio-default
source ~/prefix-3.8/setup_env.sh
python3 ~/prefix-3.8/lib/uhd/utils/uhd_images_downloader.py
```
You can test your installation by connecting your usrp and running the program for a command line fft plotter:
```
python3 ~/prefix-3.8/lib/uhd/examples/python/curses_fft.py -f 2.4e9
```

## Useful commands:
To see all locally connected usrp devices: `uhd_find_devices`

To get more information on connected usrps: `uhd_usrp_probe`