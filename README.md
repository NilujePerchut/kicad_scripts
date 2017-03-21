# kicad_scripts
Some kicad scripts

## td.py

This script adds and deletes teardrops to a PCB.<br>
Based on https://github.com/svofski/kicad-teardrops.<br>
This implementation uses zones instead of tracks. This allows to comply with DRC rules by simply rebuild all zones.
Teardrops created with this script are saved in a file named after your pcb file with the "_td" suffix in order to be able to delete them later.

**Add Teardrops:**<br>
1. Select some vias/pads on which you want to add teardrops. Or don't select anything to apply teardrops on all vias/pads<br>
2. Open the script console and type:
<br><pre>
cd path_to_the_td.py_script_location
import td
td.SetTeardrops()
</pre>
3. Rebuild all zones (by typing "b").
4. In order to make teardrops appear, just select the current canvas mode in the Display Menu.

**Delete Teardrops:**<br>
1. Open the script console and type:
<br><pre>
cd path_to_the_td.py_script_location
import td
td.RmTeardrops()
</pre>

**Notice**: SetTeardrops accepts three optional parameters: hpercent, vpercent, segs.<br>
Segs defines the number of segments in one teardrop curve (default = 10). Setting segs=2 will disable curved teardrops and use straight line instead.<br>
Vpercent (default 70%) and hpercent (default 30%) define the teardrop dimensions (relative to via/pad size) according to the Altium way (for via only):
http://techdocs.altium.com/sites/default/files/wiki_attachments/235632/TeardropsDlg.png<br>
When curved teardrops are selected (segs>2), the vpercent maximum is 70%.
