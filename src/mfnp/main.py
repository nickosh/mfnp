# Mainframe Notepad

# Copyright © 2022 Nikolay Shishov. All rights reserved.
# SPDX-License-Identifier: MIT

from pathlib import Path

import dearpygui.dearpygui as dpg
from dearpygui_ext.logger import mvLogger
from logger import LoggerHandler

APP_WORKDIR: Path = Path(__file__).resolve().parents[0]
JCLFILE_PRESEND: str = "presend.jcl"

dpg.create_context()

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


def app_load_params():
    try:
        dpg.set_value("result_wait", cfg_app.getboolean("result_wait"))
        dpg.set_value("result_details", cfg_app.getboolean("result_details"))
        dpg.set_value("config_user", cfg_remote["user"])
        dpg.set_value("config_ip", cfg_remote["ip"])
        dpg.set_value("config_port", cfg_remote.getint("port"))
        dpg.set_value("is_presend", cfg_jcl.getboolean("is_presend"))
        dpg.set_value("jcl_folder_path", cfg_jcl["jcl_folder_path"])
        dpg.set_value("jcl_file_name", cfg_jcl["jcl_file_name"])
    except Exception as e:
        msg = f"Can't load parameters from config.ini: {str(e)}"
        log.error(msg)
        raise EnvironmentError(msg)


def app_restore_env():
    if dpg.get_value("jcl_folder_path"):
        filelist_load(dpg.get_value("jcl_folder_path"))
    if dpg.get_value("jcl_file_name"):
        file_load_jcl()
        dpg.configure_item(
            "listbox_files_jcl", default_value=dpg.get_value("jcl_file_name")
        )


def app_before_exit() -> None:
    log.info("App going to exit. Bye bye.")

    cfg_app["result_wait"]: str = str(dpg.get_value("result_wait"))
    cfg_app["result_details"]: str = str(dpg.get_value("result_details"))
    cfg_remote["user"]: str = str(dpg.get_value("config_user"))
    cfg_remote["ip"]: str = str(dpg.get_value("config_ip"))
    cfg_remote["port"]: str = str(dpg.get_value("config_port"))
    cfg_jcl["is_presend"]: str = str(dpg.get_value("is_presend"))
    cfg_jcl["jcl_folder_path"]: str = str(dpg.get_value("jcl_folder_path"))
    cfg_jcl["jcl_file_name"]: str = str(dpg.get_value("jcl_file_name"))
    try:
        config_save()
    except Exception as e:
        raise EnvironmentError(f"Error while config saving: {e}")


def file_load_presend() -> None:
    presend_file: Path = Path(APP_WORKDIR, JCLFILE_PRESEND)
    if presend_file.exists():
        dpg.set_value("editor_text_presend", str(presend_file.read_text()))
        log.info("PreSend JCL file loaded")
    else:
        log.error(f"Can't found JCL presend file: {str(presend_file)}")


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


def file_save(filefolder: str, filename: str, data: str):
    jclfile: Path = Path(filefolder, filename)
    if jclfile.exists():
        jclfile.write_text(data)
        log.info(f"Changes successfully saved to file: {jclfile}")
    else:
        log.error(f"Can't save file - {jclfile} not exist")


def filelist_load(folder: str) -> None:
    files: list = list(Path(folder).glob("*.JCL"))
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


def folder_picker_open(_, data) -> None:
    selections: dict = data["selections"]
    if len(selections) > 0:
        jcl_folder_path: Path = Path(selections[next(iter(selections))])
        # Workaround for DPG's bug - duplicated folder name in selection
        # https://github.com/hoffstadt/DearPyGui/issues/1942
        jcl_folder_path = jcl_folder_path.parent
        # end of workaround
        if jcl_folder_path.exists():
            valid_path: str = str(jcl_folder_path.resolve())
            dpg.set_value("jcl_folder_path", valid_path)
            filelist_load(valid_path)
        else:
            log.error(f"Folder {str(jcl_folder_path.resolve())} not exist")
    else:
        log.error("Folder not selected")


def folder_picker_close(sender, data) -> None:
    log.info("Folder not selected")


def mf_send() -> None:
    def mf_process_start() -> None:
        dpg.configure_item("button_mf_send", enabled=False)
        dpg.configure_item("mf_job_process_group", show=True)

    def mf_process_finish() -> None:
        dpg.configure_item("mf_job_process_group", show=False)
        dpg.configure_item("button_mf_send", enabled=True)

    mf_process_start()

    config_user: str = dpg.get_value("config_user")
    config_passwd: str = dpg.get_value("config_passw")
    config_ip: str = dpg.get_value("config_ip")
    config_port: int = dpg.get_value("config_port")

    if not config_user or not config_passwd or not config_ip or not config_port:
        log.error("Missing FTP connection information")
        mf_process_finish()
        return None

    mf = MFConnector(
        user=config_user,
        passwd=config_passwd,
        ip=config_ip,
        ftp_port=config_port,
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
        log.info("All jobs processed")
    else:
        log.error("No MF connection, please check MF options!")
    mf_process_finish()


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
                no_spaces=True,
                width=180,
            )
            dpg.add_input_int(label="FTP port", source="config_port", width=100)

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
                    with dpg.group(horizontal=True, horizontal_spacing=20):
                        dpg.add_button(
                            label="Reset changes", callback=lambda: file_load_presend()
                        )
                        dpg.add_button(
                            label="Save changes",
                            tag="btn_filesave_presend",
                            callback=lambda: file_save(
                                str(APP_WORKDIR),
                                "presend.jcl",
                                str(dpg.get_value("editor_text_presend")),
                            ),
                        )
                        dpg.add_checkbox(label="Send preSend JCL", source="is_presend")
                with dpg.collapsing_header(label="JCL Editor", default_open=True):
                    dpg.add_input_text(
                        label="JCL Editor",
                        source="editor_text_main",
                        multiline=True,
                        height=310,
                    )
                    with dpg.group(horizontal=True, horizontal_spacing=20):
                        dpg.add_button(
                            label="Reset changes", callback=lambda: file_load_jcl()
                        )
                        dpg.add_button(
                            label="Save changes",
                            tag="btn_filesave_main",
                            callback=lambda: file_save(
                                str(dpg.get_value("jcl_folder_path")),
                                str(dpg.get_value("jcl_file_name")),
                                str(dpg.get_value("editor_text_main")),
                            ),
                        )
                dpg.add_separator()
                with dpg.group(horizontal=True, horizontal_spacing=20):
                    dpg.add_button(
                        label="Show results window",
                        callback=lambda: dpg.configure_item("window_result", show=True),
                    )
                    dpg.add_checkbox(label="Wait for results", source="result_wait")
                    dpg.add_checkbox(
                        label="Show detailed MF results", source="result_details"
                    )
                    dpg.add_button(
                        label="[ Send ]",
                        tag="button_mf_send",
                        callback=lambda: mf_send(),
                    )
                    with dpg.group(
                        horizontal=True,
                        horizontal_spacing=10,
                        tag="mf_job_process_group",
                        show=False,
                    ):
                        dpg.add_text(
                            default_value="In progress...",
                            color=[255, 255, 0],
                        )

    with dpg.child_window(label="logger", autosize_x=True, height=140):
        # Creation of DPG logger visual component
        uilogger: mvLogger = mvLogger(parent="logger")

with dpg.window(tag="window_result", label="MF Job Results", show=False):
    with dpg.group(horizontal=True, horizontal_spacing=20):
        dpg.add_text("PreSend Job Result:")
        dpg.add_text(source="result_mf_presend_rc")
    with dpg.group(horizontal=True, horizontal_spacing=20):
        dpg.add_text("Main Job Result:")
        dpg.add_text(source="result_mf_main_rc")
    dpg.add_input_text(
        source="result_mf_main_out",
        multiline=True,
        readonly=True,
        width=700,
        height=500,
    )


dpg.create_viewport(title="Mainframe Notepad")
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("window_main", True)

# Because of current DPG limitations logger singleton must be created after visual component
log = LoggerHandler("log", "debug", uilogger)
log.info("App started")

# Imports which uses logger singleton must be inited after singleton creation
from config import cfg_app, cfg_jcl, cfg_remote, config_save
from mfconn import MFConnector

app_load_params()
file_load_presend()
app_restore_env()

dpg.set_exit_callback(app_before_exit)
dpg.start_dearpygui()
dpg.destroy_context()
