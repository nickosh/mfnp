# Mainframe Notepad

# Copyright © 2022 Nikolay Shishov. All rights reserved.
# SPDX-License-Identifier: MIT

import dearpygui.dearpygui as dpg
from dearpygui_ext.logger import mvLogger

# from mfnp import APP_VERSION
from pathlib import Path
from logger import LoggerHandler

from mfconn import MFConnector

# from mfnp import gui

CMD_PRESEND: str = "test_presend"
APP_INIT_FILE: str = "init.ini"

dpg.create_context()
dpg.configure_app(init_file=APP_INIT_FILE)

with dpg.value_registry():
    dpg.add_string_value(default_value="", tag="jcl_folder_path")
    dpg.add_string_value(default_value="", tag="jcl_file_name")

    dpg.add_string_value(default_value="", tag="editor_text_presend")
    dpg.add_string_value(default_value="", tag="editor_text_main")

    dpg.add_bool_value(default_value=False, tag="is_presend")

    dpg.add_string_value(default_value="", tag="config_user")
    dpg.add_string_value(default_value="", tag="config_passw")
    dpg.add_string_value(default_value="0.0.0.0", tag="config_ip")
    dpg.add_int_value(default_value=21, tag="config_port")

    dpg.add_bool_value(default_value=True, tag="result_wait")
    dpg.add_bool_value(default_value=True, tag="result_details")

    dpg.add_string_value(default_value="", tag="result_mf_presend_rc")
    dpg.add_string_value(default_value="", tag="result_mf_main_rc")
    dpg.add_string_value(default_value="", tag="result_mf_main_out")


def app_before_exit() -> None:
    log.info("Application going to exit. Bye bye.")
    dpg.save_init_file(APP_INIT_FILE)


def file_load_presend() -> None:
    dpg.set_value("editor_text_presend", str(CMD_PRESEND))


def file_load_jcl() -> None:
    folder: str = dpg.get_value("jcl_folder_path")
    filename: str = dpg.get_value("jcl_file_name")
    if folder and filename:
        try:
            pfile: Path = Path(folder, filename)
            dpg.set_value("editor_text_main", pfile.read_text())
            log.info(f"File {pfile} opened in editor")
        except Exception as e:
            log.error(f"Something wrong with file opening: {e}")
    else:
        dpg.set_value("editor_text_main", "")


def filelist_load(folder: str) -> None:
    files = list(Path(folder).glob("*.JCL"))
    if len(files) > 0:
        log.info(f"{len(files)} JCL files found in {folder}")
        fnames: list = [file.name for file in files]
        dpg.configure_item("listbox_files_jcl", items=fnames)
    else:
        log.error(f"JCL files not found in {folder}")


def filelist_open_file(sender) -> None:
    if sender:
        dpg.set_value("jcl_file_name", dpg.get_value(sender))
        file_load_jcl()


def folder_picker_open(sender, data) -> None:
    selections = data["selections"]
    if len(selections) > 0:
        jcl_folder_path: Path = Path(selections[next(iter(selections))])
        # Workaround for DPG's bug - duplicated folder name in selection
        # https://github.com/hoffstadt/DearPyGui/issues/1942
        jcl_folder_path = jcl_folder_path.parent
        # end of workaround
        if jcl_folder_path.exists():
            valid_path = str(jcl_folder_path.resolve())
            dpg.set_value("jcl_folder_path", valid_path)
            filelist_load(valid_path)
        else:
            log.error(f"Folder {str(jcl_folder_path.resolve())} not exist")
    else:
        log.error("Folder not selected")


def folder_picker_close(sender, data) -> None:
    log.info("Folder not selected")


def editors_reset() -> None:
    file_load_presend()
    file_load_jcl()


def mf_send(sender):
    dpg.configure_item("button_mf_send", enabled=False)
    mf = MFConnector(
        user=dpg.get_value("config_user"),
        passwd=dpg.get_value("config_passw"),
        ip=dpg.get_value("config_ip"),
        ftp_port=dpg.get_value("config_port"),
    )
    if mf:
        presend_active: bool = dpg.get_value("is_presend")
        presend_data: str = dpg.get_value("editor_text_presend")
        if presend_active:
            if presend_data:
                presend_out = mf.send(
                    "PRECMD",
                    presend_data,
                    dpg.get_value("result_wait"),
                )
                if presend_out:
                    dpg.set_value("result_mf_presend_rc", presend_out[0])
            else:
                dpg.set_value("result_mf_presend_rc", "Skipped")
                log.warning("No PRESEND data, send skipped")
        else:
            dpg.set_value("result_mf_presend_rc", "Skipped")

        main_data: str = dpg.get_value("editor_text_main")
        if main_data:
            main_out = mf.send("MAINJB", main_data, dpg.get_value("result_wait"))
            if main_out:
                dpg.set_value("result_mf_main_rc", main_out[0])
                dpg.set_value("result_mf_main_out", main_out[1])
        else:
            dpg.set_value("result_mf_main_rc", "Skipped")
            dpg.set_value("result_mf_main_out", "")
            log.warning("No JCL data, send skipped")
        if dpg.get_value("result_details"):
            dpg.configure_item("window_result", show=True)
        log.info("All jobs sended")
    else:
        log.error("No MF connection, please check MF options!")
    dpg.configure_item("button_mf_send", enabled=True)


dpg.add_file_dialog(
    directory_selector=True,
    file_count=1,
    show=False,
    callback=folder_picker_open,
    cancel_callback=folder_picker_close,
    tag="dialog_folder_jcl",
)

with dpg.window(tag="window_main"):
    with dpg.child_window(autosize_x=True, height=35):
        with dpg.group(horizontal=True, horizontal_spacing=20):
            dpg.add_input_text(
                label="Username", source="config_user", no_spaces=True, width=150
            )
            dpg.add_input_text(
                label="Password",
                source="config_passw",
                no_spaces=True,
                password=True,
                width=150,
            )
            dpg.add_input_text(
                label="IP address",
                source="config_ip",
                default_value="0.0.0.0",
                no_spaces=True,
                width=180,
            )
            dpg.add_input_int(
                label="FTP port", source="config_port", default_value=21, width=100
            )

    with dpg.child_window(autosize_x=True, height=450):
        with dpg.group(horizontal=True, horizontal_spacing=20):
            dpg.add_button(
                label="Select JCL folder",
                callback=lambda: dpg.show_item("dialog_folder_jcl"),
            )
            with dpg.group(horizontal=True, horizontal_spacing=5):
                dpg.add_text("Current folder path: ")
                dpg.add_text(
                    source="jcl_folder_path",
                    color=[0, 255, 0],
                )
        with dpg.group(horizontal=True, horizontal_spacing=20):
            dpg.add_listbox(
                label="JCL files",
                tag="listbox_files_jcl",
                num_items=23,
                width=200,
                callback=filelist_open_file,
            )
            with dpg.group():
                with dpg.collapsing_header(label="PreSend JCL"):
                    dpg.add_input_text(
                        label="PreSend JCL",
                        source="editor_text_presend",
                        multiline=True,
                        height=340,
                    )
                with dpg.collapsing_header(label="JCL Editor", default_open=True):
                    dpg.add_input_text(
                        label="JCL Editor",
                        source="editor_text_main",
                        multiline=True,
                        height=340,
                    )
                with dpg.group(horizontal=True, horizontal_spacing=20):
                    dpg.add_button(label="Reset Editors", callback=editors_reset)
                    dpg.add_checkbox(label="Send preSend JCL", source="is_presend")
                    dpg.add_checkbox(label="Wait for results", source="result_wait")
                    dpg.add_checkbox(
                        label="Get detailed MF results", source="result_details"
                    )
                    dpg.add_button(
                        label="[ Send ]", tag="button_mf_send", callback=mf_send
                    )

    with dpg.child_window(label="logger", autosize_x=True, height=140):
        uilogger: mvLogger = mvLogger(parent="logger")

with dpg.window(tag="window_result", label="MF Job Results"):
    dpg.add_text("PreSend Job Result:")


dpg.create_viewport(title="Mainframe Notepad")
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("window_main", True)

log = LoggerHandler("log", "debug", uilogger)
log.info("App started")

dpg.set_exit_callback(app_before_exit)
dpg.start_dearpygui()
dpg.destroy_context()
