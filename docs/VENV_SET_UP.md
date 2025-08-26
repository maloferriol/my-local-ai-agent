# Setting up the virtual env

### init set-up required

1. have python installed
1.1 you can check using `python3 --version`

2. ensure pip3 is installed 
2.1 you can check using `pip3 --version`

run command to CREATE

```
python3 -m venv .venv
```

run command to ACTIVATE 
```
source .venv/bin/activate
```

echo $VIRTUAL_ENV
to disable venv use `deactivate`



Use `pip3 freeze` to update the requirements file

```
pip3 freeze > requirements.txt
```


```
pip3 install -r requirements.txt
```