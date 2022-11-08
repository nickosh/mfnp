import io
import re
import socket
from ftplib import FTP, all_errors
from time import sleep

from dearpygui import core

from .logger import LoggerHandler


class MFConnector:
    def __new__(
        cls,
        user: str,
        passwd: str,
        ip: str,
        ftp_port: int = 21,
    ):
        if not ip or not user or not passwd or not ftp_port:
            return None

        instance = super().__new__(cls)
        instance.pylog = LoggerHandler.new(__name__)
        return instance

    def __init__(
        self,
        user: str,
        passwd: str,
        ip: str,
        ftp_port: int = 21,
    ):
        self.ip = ip
        self.ftp_port = ftp_port
        self.username = user
        self.password = passwd
        self.log("info", "Starting connect initiation...")
        self.conn = self._job_connect()

    def __del__(self):
        self._ftp_done(self.conn)

    def log(self, level: str, message: str):
        if level == "info":
            self.pylog.info(message)
            core.log_info(f"{message}", logger="Output")
        elif level == "warn":
            self.pylog.warning(message)
            core.log_warning(f"{message}", logger="Output")
        elif level == "error":
            self.pylog.error(message)
            core.log_error(f"{message}", logger="Output")
        elif level == "debug":
            self.pylog.debug(message)
            core.log_debug(f"[{__name__}]: {message}", logger="Output")
        else:
            self.log("error", "Unknown logger level")

    def _ftp_connect(self, ip: str, port: int, user: str, passwd: str):
        try:
            ftp = FTP(host=ip, user=user, passwd=passwd, timeout=600)
            # ftp.set_debuglevel(2)
            self.log("info", f"We connected to {user}@{ip}:{port}")
            return ftp
        except all_errors as msg:
            self.log("error", msg)

    def _job_connect(self, job_remote_patch: str = ""):
        try:
            ftp = self._ftp_connect(
                self.ip, self.ftp_port, self.username, self.password
            )
            return ftp
        except all_errors as msg:
            self.log("error", msg)

    def _job_run(self, ftp: FTP, job_name: str, job_data: str):
        try:
            ftp.voidcmd("site filetype=JES NOJESGETBYDSN")
            sleep(1)
            self.log("info", f"Run job: {job_name}")
            reply = ftp.storlines(
                f"STOR {job_name}", io.BytesIO(job_data.encode("utf-8"))
            )
            sleep(1)
            ftp.voidcmd("site filetype=SEQ")
            id = re.search("J\\d+|JOB\\d+", reply)
            if id:
                id = id.group(0)
                return id
            else:
                self.log("error", f"Can't get job id. MF reply: {reply}")
        except socket.timeout:
            self.log("debug", "FTP connect timed out.")
        except all_errors as msg:
            self.log("error", msg)

    def _job_result(self, ftp: FTP, job_id: str, user: str):
        try:
            ftp.voidcmd("site filetype=JES NOJESGETBYDSN")
            ftp.voidcmd("site JESJOBNAME=*")
            ftp.voidcmd("site JESSTATUS=*")
            ftp.voidcmd(f"site JESOWNER={user.upper()}")
            sleep(3)
            getStatus = True
            getStatusTry = 0
            output = None
            rc = None
            while getStatus:
                getStatusTry += 1
                joblist = []
                ftp.dir(joblist.append)
                for job in joblist:
                    if f"{job_id}" in job:
                        rc = re.search(
                            r".+(RC=\d+|RC\sunknown|ABEND=\d+|JCL\serror)", job
                        )
                        if rc:
                            if rc.group(1):
                                rc = rc.group(1)
                                if rc == "RC=0000":
                                    self.log(
                                        "info",
                                        f"Job {job_id} done with {rc}.",
                                    )
                                else:
                                    self.log(
                                        "warn",
                                        f"Job {job_id} done with {rc}.",
                                    )
                                getStatus = False
                if getStatusTry > 30:
                    self.log(
                        "warn",
                        f"Job {job_id} still not done. Too many tries. Timeout.",
                    )
                    break
                if not rc:
                    timewait = 15
                    self.log(
                        "info",
                        f"Job {job_id} in work. Wait {timewait} sec and check. Try: {getStatusTry}",
                    )
                    sleep(timewait)
            output = []
            self.log(
                "info",
                "Collecting job detailed output...",
            )
            ftp.retrlines(f"RETR {job_id}.x", output.append)
            sleep(1)
            ftp.voidcmd("site filetype=SEQ")
            return [
                str(rc),
                """{}""".format("\n".join(output[1:])),
            ]
        except socket.timeout:
            self.log("debug", "FTP connect timed out.")
        except all_errors as msg:
            self.log("error", msg)

    def _ftp_done(self, ftp: FTP):
        try:
            self.log("info", "Close connection")
            ftp.quit()
        except all_errors as msg:
            self.log("error", msg)

    def send(self, job_name: str, job_data: str, results: bool = True):
        job_id = self._job_run(self.conn, job_name, job_data)
        output = ""
        if results:
            if job_id:
                output = self._job_result(self.conn, job_id, self.username)
            else:
                self.log("error", "Job not started. Something wrong!")
            return output
        else:
            return ["Without waiting for results", ""]
