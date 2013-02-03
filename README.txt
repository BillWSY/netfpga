Setup:
Install web.py by following instructions in http://webpy.org
Change MAX_PER_TIME and filedir in .py file to meet the actual demand.
Modify program.sh file. Set the correct Altera bin directory and upload file path. Change USB-Blaster name in accordance to actual situation.
Modify tcpserver.sh file. Set the correct Altera bin directory, tcl file path and tcp server log file path.
Make sure TCP port 1337 is not occupied. Or choose another port and modify both .tcl and .py file.
Run ./netfpga.py

General flow:
1. [/new]Start a new session. This would change the current status to PROTECTED. Before protection expires no one can create a new session. The session ID is stored in user's cookie.
2. [/upload]Upload .sof file. This file would be saved as current.sof in upload_files folder. If necessary it could be copied as session_id.sof.
3. [/program]Program FPGA. This would call program.sh script and download current.sof to board.
4. [/startserver]Start TCP server by calling tcpserver.sh script. It would run in background.
5. [/inittarget]Reset the core by asserting and then deasserting global reset signal bit in virtual jtag input.
6. [/interaction]Communicate with the core. Page will refresh every second.
7. [/giveup]Give up current session and set the status to IDLE.

