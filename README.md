# hemodynamic_monitor

Overview: 

This program was written and designed to read continuoius hemodynamic data from a RS-232 to USB serial adapter from different instruments and wireless transmit the data over wifi to Redcap database.

Files: 

logger.py: the base file for execution of the program to run contiuously. Loads the other files and shuffles data between the serial port and the database.

serial_wrapper.py: a wrapper for the serial connections which are broken out into NIRS connection and Swan-Ganz connection. Currently designed for the following inputs.
- Vigilence II (Edwards Lifesciences): port A, IFMout, baudrate 9600, using a RS-232 to USB serial adapter with TX/RX switch
- Casmed NIRS monitor (Formerly Casmed, now Edwards life sciences): port A, 4-channel CSV (first two columns are the nirs probes, upper and lower), baudrate 9600, using a RS-232 to USB serial adapter (no need for the TX/RX switch).
- Hemosphere (Edwards Lifesciences): port A, IFMout, baudrate 9600. Also has USB output (the rear USB) which uses a USB to RS-232 adapter then RS-232 male-to-female adapter with TX/TX switch, and finally RS-232 to USB serial adapter. The USB output has to be configured as 4-channel output with the last two columns as the nirs (upper and lower, respectively). Hemosphere has built in NIRS and Swan collector.

redcap.py: this is a wrapper for the http commands for posting records to RedCap as data is recieved. The program also collates the two asynchronous input datastreams with resolution down to the second.

Hardware:

This was desisnged and built for a raspberry pi zero with a wireless (WifI) connection which must be configured prior to running.
