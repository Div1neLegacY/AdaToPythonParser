Install Alire. This will grab all Adacore source via a public crate

```
sudo apt update
sudo apt install -y curl unzip
curl --proto '=https' -sSf https://www.getada.dev/init.sh | sh
```

Reload shell

```
source ~/.profile 2>/dev/null || true
source ~/.bashrc 2>/dev/null || true
```

Change directory into project

```
cd libadalang_parser
```

Get libadalang crate

```
alr get libadalang=24.0.0
```

Create Python venv for package installation

```
sudo apt install -y python3-pip python3.12-venv
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel
```

Build libadalang crate and install the Python module in venv

```
cd libadalang_*
LIBRARY_TYPE=relocatable alr build
cd python
pip install .
cd ..
export LD_LIBRARY_PATH="$PWD/lib/relocatable/dev:$LD_LIBRARY_PATH"
```

Test libadalang via PyPi package

```
python3

>>> import libadalang as lal
```