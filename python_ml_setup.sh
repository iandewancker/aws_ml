#!/bin/bash
sudo apt-get update && sudo apt-get -yq upgrade
sudo apt-get install python-dev
sudo apt-get install -y libopencv-dev python-opencv libhdf5-dev
sudo apt-get install -yq linux-image-extra-`uname -r`
sudo apt-get -y install git
sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran
sudo apt-get install python-pip

sudo pip install -q --upgrade pip
sudo pip install -U numpy
sudo pip install -U scipy
sudo pip install scikit-learn==0.17 
sudo pip install joblib 
sudo pip install sigopt 
sudo pip install pystache
sudo pip install awscli
sudo pip install boto
sudo pip install hyperopt
sudo pip install pymongo
sudo pip install networkx
sudo pip install h5py
sudo pip install --upgrade pillow
sudo pip install pycuda
sudo pip install scikit-cuda==0.5.1
sudo pip install pytools
sudo pip install scikit-image
sudo pip install autograd
sudo apt-get install libjpeg-dev zlib1g-dev

wget http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers/cuda-repo-ubuntu1404-7-5-local_7.5-18_amd64.deb
sudo dpkg -i cuda-repo-ubuntu1404-7-5-local_7.5-18_amd64.deb
sudo apt-get update
sudo apt-get -yq install cuda

# tensorFlow CPU
#sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-0.7.1-cp27-none-linux_x86_64.whl
# tensorFlow GPU
sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.7.1-cp27-none-linux_x86_64.whl
