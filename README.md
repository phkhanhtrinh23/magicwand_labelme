Follow the step-by-step instructions below:

1. Setup conda
```
conda create --name labelme2 python=3.9
conda activate labelme2
```

2. Install the requirement dependencies
```
pip install .
pip install opencv-python
pip install pyinstaller
pyinstaller labelme.spec
```

3. Execute the code:

Go to `./labelme/labelme`
```
python __main__.py
```
