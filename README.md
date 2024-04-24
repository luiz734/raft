## Requirements
Python and pip

## Setup
- Initialize venv
```
pip install virtualenv &&\
python3 -m venv venv &&\
chmod +x venv/bin/activate && source venv/bin/activate
```
- Install Pyro `pip install Pyro5`


## Commands
Run nameserver `python -m Pyro5.nameserver`
Show nameservers running `python -m Pyro5.nsc list`

