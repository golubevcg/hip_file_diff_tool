import hou

source_path = "C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source_edited.hipnc"
target_path = "C:/Users/golub/Documents/hip_file_diff_tool/test_scenes/billowy_smoke_source.hipnc"

hou.hipFile.load(source_path)
all_nodes_data_from_source = {}

for object in hou.node("/").allNodes():
    path = object.path()

    parms = object.parms()
    if not parms:
        continue
    
    parms_and_values = {}
    for parm in parms:
        name = parm.name()
        val = parm.eval()
        parms_and_values[name] = val  

    all_nodes_data_from_source[path] = parms_and_values

hou.hipFile.clear()

hou.hipFile.load(target_path)
for obj in hou.node("/").allNodes():
    path = obj.path()
    parms = obj.parms()

    if path in all_nodes_data_from_source:
        values = all_nodes_data_from_source[path]