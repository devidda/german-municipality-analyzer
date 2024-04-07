# Install cmake
#  https://www.linuxcapable.com/how-to-install-cmake-on-debian-linux/#step-2-install-cmake-on-debian-12-11-or-10-via-apt-command
sudo apt update && sudo apt upgrade -y \
    && sudo apt install cmake -y

cd /workspaces/thesis/geo-libs/
sudo apt-get install -y \
    binutils=2.35.* \
    libproj-dev=7.2.* \

# Download GDAL
# https://docs.djangoproject.com/en/3.2/ref/contrib/gis/install/geolibs/#gdal
wget https://download.osgeo.org/gdal/3.8.3/gdal-3.8.3.tar.gz \
    && tar xzf gdal-3.8.3.tar.gz \
    && rm gdal-3.8.3.tar.gz \


# Build and install GDAL
# https://gdal.org/development/building_from_source.html
cd gdal-3.8.3
mkdir build
cd build && cmake .. \
    && cmake --build . \
    && sudo cmake --build . --target install

# Set the environment variable
export LD_LIBRARY_PATH=/workspaces/thesis/geo-libs/gdal-3.8.3/build/:$LD_LIBRARY_PATH
