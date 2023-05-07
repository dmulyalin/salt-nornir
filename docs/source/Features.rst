Features
========

Salt-Nornir supports extensive list of features, this page is an attempt
to classify and orginize them for the ease of search, usage and clarification
on what versions support what features.

Interact with devices Command Line
----------------------------------

+---------------------------------------------------------------------+---------+---------+
| Feature                                                             | 0.19.*  | 0.18.*  |
+=====================================================================+=========+=========+
| send single show command to multiple devices                        |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| send multiple show commands to devices                              |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands in a loop                                     |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands in a loop until pattern                       |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| save show commands output to a file on mionion                      |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands using Netmiko                                 |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands using Netmiko timing method                   |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands using NAPALM                                  |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands using Scrapli                                 |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| collect show commands using PyATS                                   |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| send multiline string using ``_br_`` as a new line                  |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| source show commands to colect from inline template                 |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| source show commands to collect from template on Master             |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| source per-device show commands from template on Master             |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| parse show commands output using TTP with Netmiko                   |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| parse show commands output using TTP with Scrapli                   |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| parse show commands output using NAPALM getters                     |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| parse show commands output using PyATS parsers                      |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+
| parse show commands output using TTP with Netmiko                   |  YES    |  YES    |
+---------------------------------------------------------------------+---------+---------+