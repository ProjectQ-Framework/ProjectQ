#!/usr/bin/env bash
# Run inside the CentOS container; checkout and other Node actions run on the host.
set -euo pipefail

if [[ "$CENTOS_VERSION" == 7 ]]; then
    vault_version=7.9.2009
else
    vault_version=8.5.2111
fi

# Both CentOS releases have moved from the live mirrors to the vault.
sed -i \
    -e 's|^mirrorlist=|#mirrorlist=|' \
    -e "s|^#baseurl=http://mirror.centos.org/centos/\$releasever|baseurl=https://vault.centos.org/$vault_version|" \
    -e 's|^#baseurl=http://mirror.centos.org/$contentdir/$releasever|baseurl=https://vault.centos.org/'"$vault_version"'|' \
    /etc/yum.repos.d/CentOS-*.repo
yum update -y

if [[ "$CENTOS_VERSION" == 7 ]]; then
    yum install -y centos-release-scl-rh
    sed -i \
        -e 's|^mirrorlist=|#mirrorlist=|' \
        -e 's|^#baseurl=http://mirror.centos.org/centos/7|baseurl=https://vault.centos.org/7.9.2009|' \
        /etc/yum.repos.d/CentOS-SCLo-scl-rh.repo
    yum install -y https://packages.endpointdev.com/rhel/7/os/x86_64/endpoint-repo.x86_64.rpm
    yum install -y --enablerepo=centos-sclo-rh rh-python38-python-pip rh-python38-python-devel
    export PATH="/opt/rh/rh-python38/root/usr/bin:$PATH"
    export LD_LIBRARY_PATH="/opt/rh/rh-python38/root/usr/lib64:${LD_LIBRARY_PATH:-}"
else
    yum install -y python38-devel
fi

yum install -y git gcc-c++ make
git config --global --add safe.directory /src
python3 -m pip install -U pip setuptools wheel
python3 setup.py gen_reqfile --include-extras=test,azure-quantum,braket
python3 -m pip install -r requirements.txt --prefer-binary
python3 -m pip install -ve '.[azure-quantum,braket,test]'
echo 'backend: Agg' > matplotlibrc
python3 -m pytest -p no:warnings
