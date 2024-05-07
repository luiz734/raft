## Setup
### Environment
- Install [direnv]( https://github.com/direnv/direnv/blob/master/docs/installation.md )
- Install [tmux]( https://github.com/tmux/tmux )
    - Use the shorcut `C-b+&` and type `y` to kill the current session
- Install [tmuxinator]( https://github.com/tmuxinator/tmuxinator )
    - Copy the file `peers.yml` to `~/.config/tmuxinator`

Also make sure `python` and `pip` are installed.

### Python dependecies
`pip install Pyro5 rich`

## Running
- Run the nameserver `python -m Pyro5.nameserver`.
- By using tmuxinator + direnv, the `.envrc` should load the pip envirotment.
- Running `tmuxinator peers` will create a tmux session with 4 panes, one for each peer.
You can edit the parameters on each peer by editing the `peers.yml` file.
- You can use the shorcut `C-b+&` to easily close all panes and kill the server.
- Send messages from the client to the leader by running `python client.py <YOUR_MESSAGE>`

### Tips
- If you don't want to use the shorcut, run `tmux kill-session -t peers`. It will do the same thing.
