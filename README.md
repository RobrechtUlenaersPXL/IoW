# README #
# installation/patching

excecute git clone -b test https://github.com/RobrechtUlenaersPXL/IoW.git 

* in the ./documents/IoW directory execute ./IowPatchscript.sh
* should install all necessary files
* reboot after script => hotspot is setup upon reboot
* after filling in network info reboot again to startup service
* crontab job should check for new code every day at 02am

## how to acces terminal
* crontab starts a tmux session
* all services run in this tmux session
* to acces it run the following command:
* tmux attach-session -t iow
* to leave use keys ctrl+b then D to detach
* ctrl+b then X to delete session if necessary


