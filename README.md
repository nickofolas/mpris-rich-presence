# MPRIS Rich Presence
This program allows MPRIS-compatible players to communicate with Discord's IPC, and generate rich presences via Playerctl.

<p>
  <img src="https://i.imgur.com/YYgd4f3.png" height="150px">
  <img src="https://i.imgur.com/z09rwDf.png" height="150px">
</p>

<h2>Prerequisites</h2>
The following will describe how to install and use the program.

**Requirements**
* [Playerctl](https://github.com/altdesktop/playerctl)
* PyGObject
  * There's no one way to install this, so please refer to its installation documentation [here](https://pygobject.readthedocs.io/en/latest/getting_started.html)

Once you have those both installed, then you're ready to install the program itself.

<h2>Installation</h2>
<code>
pip install -U https://github.com/nickofolas/mpris-rich-presence/archive/master.zip
</code>
The use of a virtual environment is optional.

<h2>Usage</h2>
This program can be run in both interactive and uninteractive ways.

<h4>Interactive</h4>
By simply calling <code>mpris-rich-presence</code> (or <code>python -m mpris_rich_presence</code> if it wasn't added to your $PATH), an interactive version of the script will be launched, which lets you choose which media player (out of the currently running players) will be monitored for rich presence. Selecting 0 (the default) will let the program automatically switch the monitored player based on which it detects to be active.

<h4>Uninteractive</h4>
By calling the program with the <code>--auto</code> flag appended, it will run completely autonomously, using the same logic as the "auto" option from the interactive mode. This is useful if you want the program to be autostarted.

