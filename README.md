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

Note that you will need to source the setup_env.sh everytime you open a terminal. So it is recommended to copy the command `source ~/prefix-3.8/setup_env.sh` into your ~/.bashrc with the command:
```
echo "source ~/prefix-3.8/setup_env.sh" >> ~/.bashrc
```

## Useful commands:
To see all locally connected usrp devices: `uhd_find_devices`

To get more information on connected usrps: `uhd_usrp_probe`

## Troubleshooting

### gnu-radio building
If you get the error:
```
error: ‘get_system_time’ is not a member of ‘uhd::time_spec_t’
       result = uhd::time_spec_t::get_system_time();
```
When trying to run the command `pybombs prefix init ~/prefix-3.8 -R gnuradio-default`

### uhd_find_devices
If you get the error
```
[ERROR] [USB] USB open failed: insufficient permissions.

```
When trying to run `uhd_find_devices`, then run the commands:
```
sudo cp ~/prefix-3.8/src/uhd/host/utils/uhd-usrp.rules /etc/udev/rules.d/

sudo udevadm control --reload-rules

sudo udevadm trigger
```

