import io
import re
import socket
from ftplib import FTP, all_errors
from time import sleep
from typing import Optional

import dearpygui.dearpygui as dpg

from logger import LoggerHandler


class MFConnector:
    def __init__(
        self,
        user: str,
        passwd: str,
        ip: str,
        ftp_port: int = 21,
    ) -> None:
        self.ip = ip
        self.ftp_port = ftp_port
        self.username = user
        self.password = passwd
        self.log = LoggerHandler(__name__)
        self.conn = self._job_connect()

    def __del__(self) -> None:
        self._ftp_done(self.conn)

    def _ftp_connect(self, ip: str, port: int, user: str, passwd: str) -> FTP:
        try:
            ftp = FTP(host=ip, user=user, passwd=passwd, timeout=600)
            # ftp.set_debuglevel(2)
            self.log.info(f"We connected to {user}@{ip}:{port}")
            return ftp
        except all_errors as msg:
            self.log.error(str(msg))

    def _job_connect(self) -> FTP:
        try:
            ftp = self._ftp_connect(
                self.ip, self.ftp_port, self.username, self.password
            )
            return ftp
        except all_errors as msg:
            self.log.error(str(msg))

    def _job_run(self, ftp: FTP, job_name: str, job_data: str) -> Optional[str]:
        if ftp:
            try:
                ftp.voidcmd("NOOP")
            except all_errors as msg:
                self.log.error(str(msg))
                return None
        else:
            self.log.error("FTP connection not established")
            return None
        try:
            ftp.voidcmd("site filetype=JES NOJESGETBYDSN")
            sleep(1)
            self.log.info(f"Run job: {job_name}")
            reply = ftp.storlines(
                f"STOR {job_name}", io.BytesIO(job_data.encode("utf-8"))
            )
            sleep(1)
            ftp.voidcmd("site filetype=SEQ")
            job_id = re.search("J\\d+|JOB\\d+", reply)
            if job_id:
                job_id = job_id.group(0)
                return job_id
            else:
                self.log.error(f"Can't get job id. MF reply: {reply}")
        except socket.timeout:
            self.log.debug("FTP connect timed out.")
        except all_errors as msg:
            self.log.error(str(msg))

    def _job_result(self, ftp: FTP, job_id: str, user: str) -> list:
        try:
            ftp.voidcmd("site filetype=JES NOJESGETBYDSN")
            ftp.voidcmd("site JESJOBNAME=*")
            ftp.voidcmd("site JESSTATUS=*")
            ftp.voidcmd(f"site JESOWNER={user.upper()}")
            sleep(3)
            get_status: bool = True
            get_status_try: int = 0
            output = None
            rc = None
            while get_status:
                get_status_try += 1
                joblist = []
                ftp.dir(joblist.append)
                for job in joblist:
                    if str(job_id) in job:
                        rc = re.search(
                            r".+(RC=\d+|RC\sunknown|ABEND=\d+|JCL\serror)", job
                        )
                        if rc and rc.group(1):
                            rc = rc.group(1)
                            if rc == "RC=0000":
                                self.log.info(f"Job {job_id} done with {rc}.")
                            else:
                                self.log.warning(f"Job {job_id} done with {rc}.")
                            get_status = False
                if get_status_try > 30:
                    self.log.warning(
                        f"Job {job_id} still not done. Too many tries. Timeout.",
                    )
                    break
                if not rc:
                    timewait = 15
                    self.log.info(
                        f"Job {job_id} in work. Wait {timewait} sec and check. Try: {get_status_try}"
                    )
                    sleep(timewait)
            output = []
            self.log.info("Collecting job detailed output...")
            ftp.retrlines(f"RETR {job_id}.x", output.append)
            sleep(1)
            ftp.voidcmd("site filetype=SEQ")
            return [
                str(rc),
                """{}""".format("\n".join(output[1:])),
            ]
        except socket.timeout:
            self.log.debug("FTP connect timed out")
        except all_errors as msg:
            self.log.error(str(msg))

    def _ftp_done(self, ftp: FTP) -> None:
        try:
            self.log.info("Close connection")
            ftp.quit()
        except all_errors as msg:
            self.log.error(str(msg))

    def send(
        self, job_name: str, job_data: str, results: bool = True
    ) -> Optional[list]:
        job_id = self._job_run(self.conn, job_name, job_data)
        if not job_id:
            return None
        if results:
            if job_id:
                output: list = self._job_result(self.conn, job_id, self.username)
            else:
                self.log.error("Job not started. Something wrong!")
            return output
        else:
            return ["Without waiting for results", ""]
