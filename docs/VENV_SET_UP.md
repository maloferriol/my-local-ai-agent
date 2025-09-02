# Setting up the Project

## Prerequisites

* Python installed: `python3 --version`
* Pip3 installed: `pip3 --version`

## Setting up the virtual environment

### Creating the virtual environment

Run the following command to create the virtual environment:

```lang=shell
python3 -m venv .venv
```

### Activating the virtual environment

Run the following command to activate the virtual environment:

```lang=shell
source .venv/bin/activate
```

**Verification:**

```lang=shell
echo $VIRTUAL_ENV
```

**Deactivating the virtual environment:**

```lang=shell
deactivate
```

## Installing dependencies

Install the dependencies from the requirements file:

```lang=shell
pip3 install -r requirements.txt
```

Run the following command to update the requirements file:

```lang=shell
pip3 freeze > requirements.txt
```
