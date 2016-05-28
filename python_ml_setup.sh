#!/bin/bash
sudo apt-get update && sudo apt-get -yq upgrade
sudo apt-get install -y python-dev
sudo apt-get install -y libopencv-dev python-opencv libhdf5-dev
sudo apt-get install -yq linux-image-extra-`uname -r`
sudo apt-get install -y git
sudo apt-get install -y libblas-dev liblapack-dev libatlas-base-dev gfortran
sudo apt-get install -y python-pip
sudo apt-get install -y ipython
sudo apt-get install -y swig

sudo pip install -q --upgrade pip
sudo pip install -U numpy
sudo pip install -U scipy
sudo pip install scikit-learn==0.17 
sudo pip install gensim
sudo pip install pymc
sudo pip install xgboost
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
sudo pip install pandas
sudo apt-get install -y libjpeg-dev zlib1g-dev

# install CUDA
wget http://developer.download.nvidia.com/compute/cuda/7.5/Prod/local_installers/cuda-repo-ubuntu1404-7-5-local_7.5-18_amd64.deb
sudo dpkg -i cuda-repo-ubuntu1404-7-5-local_7.5-18_amd64.deb
sudo apt-get update
sudo apt-get -yq install cuda

# install cuDNN
wget https://s3-eu-west-1.amazonaws.com/christopherbourez/public/cudnn-6.5-linux-x64-v2.tgz
tar xvzf cudnn-6.5-linux-x64-v2.tgz
sudo cp cudnn-6.5-linux-x64-v2/cudnn.h /usr/local/cuda-7.5/include/
sudo cp cudnn-6.5-linux-x64-v2/libcudnn* /usr/local/cuda-7.5/lib64/

sudo ln -sf /usr/local/cuda-7.5/bin/nvcc /usr/bin/nvcc
export LD_LIBRARY_PATH=/usr/local/cuda-7.5/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-7.5/bin:$PATH

# nvidia keeps this file under lock and key for some reason
# wget https://developer.nvidia.com/rdp/assets/cudnn-7.5-linux-x64-v5.0-ga.tgz
tar xvzf cudnn-7.5-linux-x64-v5.0-ga.tgz
sudo cp cuda/include/cudnn.h /usr/local/cuda-7.5/include/
sudo cp cuda/lib64/libcudnn* /usr/local/cuda-7.5/lib64/

# compile TensorFlow so plays nice with AWS GPUs
git clone --recurse-submodules https://github.com/tensorflow/tensorflow
cd tensorflow
TF_UNOFFICIAL_SETTING=1 printf "\n \n y\n \n \n \n \n \n 3.0\n" | ./configure

# install bazel to build tensorFlow with GPU support
sudo add-apt-repository -y ppa:webupd8team/java
sudo apt-get update
echo debconf shared/accepted-oracle-license-v1-1 select true | sudo debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | sudo debconf-set-selections
sudo apt-get install -y oracle-java8-installer
sudo apt-get install -y pkg-config zip g++ zlib1g-dev
wget https://github.com/bazelbuild/bazel/releases/download/0.2.3/bazel-0.2.3-installer-linux-x86_64.sh
chmod +x bazel-0.2.3-installer-linux-x86_64.sh
./bazel-0.2.3-installer-linux-x86_64.sh --user
rm bazel-0.2.3-installer-linux-x86_64.sh
export PATH=/home/ubuntu/bin:$PATH
sudo ln -sf /usr/local/cuda-7.5/bin/nvcc /usr/bin/nvcc
export LD_LIBRARY_PATH=/usr/local/cuda-7.5/lib64:$LD_LIBRARY_PATH
export PATH=/usr/local/cuda-7.5/bin:$PATH

bazel build -c opt --config=cuda //tensorflow/tools/pip_package:build_pip_package
bazel-bin/tensorflow/tools/pip_package/build_pip_package /tmp/tensorflow_pkg
pip install /tmp/tensorflow_pkg/tensorflow-0.8.0-py2-none-any.whl

sudo pip install -y pycuda
sudo pip install -y scikit-cuda==0.5.1

# tensorFlow CPU
#sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/cpu/tensorflow-0.7.1-cp27-none-linux_x86_64.whl
# tensorFlow GPU
# sudo pip install --upgrade https://storage.googleapis.com/tensorflow/linux/gpu/tensorflow-0.7.1-cp27-none-linux_x86_64.whl
