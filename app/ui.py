from pathlib import Path

from dearpygui import core, simple

from app.init import version
from app.mfconn import MFConnector
from app.templates import presendCommand


def getJclFiles(folder):
    files = list(Path(folder).glob("*.JCL"))
    if len(files) > 0:
        core.log_info(f"{len(files)} JCL files found in {folder}", logger="Output")
        fnames = []
        for file in files:
            fnames.append(file.name)
        core.configure_item("JCL files", items=fnames)
    else:
        core.log_error(f"JCL files not found in {folder}", logger="Output")


def openJclFile(sender):
    folder = core.get_value("folder_path")
    files = list(Path(folder).glob("*.JCL"))
    if files:
        pfile = Path(files[core.get_value(sender)])
        data = pfile.read_text()
        core.set_value("JCLtext", data)
        core.log_info(f"File {pfile} opened in editor", logger="Output")
    else:
        core.log_error("No parsed file names detected", logger="Output")


def sendJob(sender):
    core.configure_item("Send", enabled=False)
    mf = MFConnector(
        core.get_value("Username"),
        core.get_value("Password"),
        core.get_value("Address"),
        core.get_value("FTP port"),
    )
    if mf:
        core.set_value("mfPreRC", "")
        core.set_value("mfMainRC", "")
        core.set_value("mfMainOut", "")
        if core.get_value("PRESENDtext"):
            preOUT = mf.send(
                "PRECMD",
                core.get_value("PRESENDtext"),
                core.get_value("Wait for results"),
            )
            if preOUT:
                core.set_value("mfPreRC", preOUT[0]),
        else:
            core.set_value("mfPreRC", "Skipped")
            core.log_warning("No PRESEND data, send skipped", logger="Output")
        if core.get_value("JCLtext"):
            mainOut = mf.send(
                "MAINJB", core.get_value("JCLtext"), core.get_value("Wait for results")
            )
            if mainOut:
                core.set_value("mfMainRC", mainOut[0])
                core.set_value("mfMainOut", mainOut[1])
        else:
            core.set_value("mfMainRC", "Skipped")
            core.set_value("mfMainOut", "")
            core.log_warning("No JCL data, send skipped", logger="Output")
        if core.get_value("Get detailed MF results"):
            core.configure_item("MF Job Results", show=True)
        core.log_info("All jobs sended", logger="Output")
    else:
        core.log_error("No MF connection, please check MF options!", logger="Output")
    core.configure_item("Send", enabled=True)


def resetEditors():
    core.set_value("PRESENDtext", presendCommand)
    if core.get_value("folder_path"):
        openJclFile("JCL files")
    else:
        core.set_value("JCLtext", "")


def directory_picker(sender, data):
    core.select_directory_dialog(callback=apply_selected_directory)


def apply_selected_directory(sender, data):
    directory = data[0]
    folder = data[1]
    folderPath = f"{directory}\\{folder}"
    core.set_value("directory", directory)
    core.set_value("folder", folder)
    core.set_value("folder_path", folderPath)
    getJclFiles(folderPath)


with simple.window("Main"):
    with simple.collapsing_header("MF Options", default_open=True):
        with simple.managed_columns("mfCol", 4):
            core.add_input_text("Username", no_spaces=True)
            core.add_input_text("Password", no_spaces=True, password=True)
            core.add_input_text("Address", default_value="0.0.0.0", no_spaces=True)
            core.add_input_int("FTP port", default_value=21, width=100)

    with simple.collapsing_header("JCL Workspace", default_open=True):
        core.add_button("Select JCL directory", callback=directory_picker)
        core.add_same_line()
        core.add_text("Directory Path: ")
        core.add_same_line()
        core.add_label_text("##dir", source="directory", color=[0, 255, 0])
        core.add_same_line()
        core.add_text("Folder: ")
        core.add_same_line()
        core.add_label_text("##folder", source="folder", color=[0, 255, 0])
        core.add_same_line()
        core.add_text("Folder Path: ")
        core.add_same_line()
        core.add_label_text("##folderpath", source="folder_path", color=[0, 255, 0])

        core.add_separator()

        with simple.managed_columns("filesCol", 2):
            core.set_managed_column_width("filesCol", 0, 250)
            core.set_managed_column_width("filesCol", 1, 800)
            core.add_listbox("JCL files", num_items=34, callback=openJclFile)
            with simple.group("editorsGroup"):
                core.add_input_text(
                    "PreSend Command", source="PRESENDtext", multiline=True, width=680
                )
                core.add_input_text(
                    "JCL Editor",
                    source="JCLtext",
                    multiline=True,
                    width=680,
                    height=450,
                )
                core.add_button("Reset Editors", callback=resetEditors)
                core.add_same_line()
                core.add_checkbox("Wait for results", default_value=True)
                core.add_same_line()
                core.add_checkbox("Get detailed MF results", default_value=True)
                core.add_same_line()
                core.add_button("Send", callback=sendJob)
                core.set_value("PRESENDtext", presendCommand)

    core.add_separator()

    with simple.collapsing_header("Results", default_open=True):
        core.add_logger("Output", autosize_x=True, autosize_y=True)

with simple.window(
    "MF Job Results",
    autosize=True,
    show=False,
):
    core.add_text("PreSend Job Result:")
    core.add_same_line()
    core.add_label_text("##MfPreRc", source="mfPreRC")
    core.add_text("Main Job Result:")
    core.add_same_line()
    core.add_label_text("##MfManRc", source="mfMainRC")
    core.add_input_text(
        "MfManOutput",
        source="mfMainOut",
        multiline=True,
        readonly=True,
        width=700,
        height=500,
    )

core.set_main_window_title(f"Mainframe Notepad {version}")
core.set_main_window_size(1200, 890)
core.set_primary_window("Main", True)
core.log_info("Program started", logger="Output")
