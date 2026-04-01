# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------
# MultiAV scanner wrapper version 0.0.1
# Copyright (c) 2014, Joxean Koret
#
# License:
#
# MultiAV is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# MultiAV is distributed in the hope that it will be  useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser Public License for more details.
#
# You should have received a copy of the GNU Lesser Public License
# along with DoctestAll.  If not, see
# <http://www.gnu.org/licenses/>.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>
#
# Description:
#
# This script implements a very basic wrapper around various AV engines
# available for Linux using their command line scanners with the only
# exception of ClamAV. The currently supported AV engines are listed
# below:
#
#   * ClamAV (Fast)
#   * F-Prot (Fast)
#   * Comodo (Fast)
#   * BitDefender (Medium)
#   * ESET (Slow)
#   * Avira (Slow)
#   * Sophos (Medium)
#   * Avast (Fast)
#   * AVG (Fast)
#   * DrWeb (Slow)
#   * McAfee (Very slow, only enabled when running all the engines)
#   * Ikarus (Medium, using wine in Linux/Unix)
#   * F-Secure (Fast)
#   * Kaspersky (Fast)
#   * Zoner Antivirus (Fast)
#   * MicroWorld-eScan (Fast)
#   * Cyren (Fast)
#   * QuickHeal (Fast)
#
# Support for the Kaspersky AV engine includes MacOSX, Windows, and Linux
#
# Features:
#
#   * Parallel scan, by default, based on the number of CPUs.
#   * Analysis by AV engine speed.
#
# -----------------------------------------------------------------------

import os
import sys
import re
import codecs
import time
import requests
from glob import glob
from datetime import datetime
from configparser import ConfigParser
from pathlib import Path
from functions.common import bcolors

from tempfile import NamedTemporaryFile
import subprocess
from subprocess import check_output, CalledProcessError, call
from multiprocessing import Process, Queue, cpu_count

try:
    import pyclamd
    has_clamd = True
except ImportError:
    has_clamd = False

# -----------------------------------------------------------------------
AV_SPEED_ALL = 3  # Run only when all engines must be executed
AV_SPEED_SLOW = 2
AV_SPEED_MEDIUM = 1
AV_SPEED_FAST = 0
AV_SPEED_ULTRA = -1

# -----------------------------------------------------------------------


class CAvScanner:
    def __init__(self, cfg_parser):
        self.cfg_parser = cfg_parser
        self.name = None
        self.speed = AV_SPEED_SLOW
        self.results = {}
        self.pattern = None
        self.file_index = 0
        self.malware_index = 1

    def build_cmd(self, path):
        parser = self.cfg_parser
        scan_path = parser.get(self.name, "PATH")
        scan_args = parser.get(self.name, "ARGUMENTS")
        scan_args = os.path.expandvars(scan_args)
        args = [scan_path]
        args.extend(scan_args.split(" "))
        args.append(path)
        return args

    def version(self):
        try:
            parser = self.cfg_parser
            cdm_args = '--version'
            cmd_path = parser.get(self.name, "PATH") 
            cmd = [cmd_path]
            cmd.extend(cdm_args.split(" "))

        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"version - Exception occured while getting version: {e}")
            print(f"Version cmd: {cmd}")
            # pass

        try:
            p1 = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
            output, error = p1.communicate()
            # print(f"Version output: {output}")
            exit_status = p1.returncode
            # print(f"version Status Code: {exit_status}")
            return output
        except Exception as e:
            print(f"Exception occured during scan: {e}")
            # except CalledProcessError as e:
            #  output = e.output

    def scan(self, path):
        if self.pattern is None:
            Exception("Not implemented")
        cmd = ''
        try:
            cmd = self.build_cmd(path)
        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"scanner - Exception occured while scanning: {e}, path: {path}")
            print(f"Scan cmd: {cmd}")
            # pass

        try:
            # print(f"Before check_output scan cmd: {cmd}")
            # output = check_output(cmd, stderr=subprocess.STDOUT, shell=True)
            p1 = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE, universal_newlines=True)
            output, error = p1.communicate()
            # print(f"After check_output scan error: {error} output: {output}")
            exit_status = p1.returncode
            # print(f"Scan Status Code: {exit_status}")
            pattern = self.pattern
            matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                self.results[match[self.file_index]] = match[self.malware_index]
            return len(self.results) > 0
        except Exception as e:
            print(f"Exception occured during scan: {e}")
            # except CalledProcessError as e:
            #  output = e.output

    def is_disabled(self):
        # parser = self.cfg_parser
        try:
            ret = self.cfg_parser.getboolean(self.name, "DISABLED")
            if ret:
                return True
            else:
                return False
        except Exception:
            return False

# -----------------------------------------------------------------------


class CTrendmicroScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Trendmicro"
        # It seems as fast as kaspersky even faster
        self.speed = AV_SPEED_FAST
        self.pattern1 = "\\nfilename=(.*)"
        self.pattern2 = "\\nvirus_name=(.*)"

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        if self.pattern is None:
            Exception("Not implemented")
        cmd = ''
        try:
            cmd = self.build_cmd(path)
        except Exception:
            e = sys.exc_info()[0]
            print("[ERROR] in build_cmd %s " % e)
            # pass

        logdir = '/var/log/TrendMicro/SProtectLinux'
        logfile = logdir+'/Virus.' + time.strftime('%Y%m%d') + '.0001'
        # print(f"Scan Command : %s " % (cmd))
        call(cmd)

        with open(logfile, 'r') as log:
            output = log.read()
        reset = open(logfile, 'wb')  # Clear the log file
        reset.close()

        matches1 = re.findall(self.pattern1, output, re.IGNORECASE | re.MULTILINE)
        matches2 = re.findall(self.pattern2, output, re.IGNORECASE | re.MULTILINE)
        for i in range(len(matches1)):
            self.results[matches1[i].split(' (')[0]] = matches2[i]

        return len(self.results) > 0
# -----------------------------------------------------------------------


class CComodoScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Comodo"
        self.speed = AV_SPEED_FAST
        self.pattern = "(.*) ---> Found .*, Malware Name is (.*)"

    def version(self):
        result = "not implemented"
        return result

    def build_cmd(self, path):
        parser = self.cfg_parser
        scan_path = parser.get(self.name, "PATH")
        scan_args = parser.get(self.name, "ARGUMENTS")
        args = [scan_path]
        args.extend(scan_args.replace("$FILE", path).split(" "))
        return args

# -----------------------------------------------------------------------


class CCyrenScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Cyren"
        self.speed = AV_SPEED_ULTRA
        self.pattern = "Found:(.*)[\s]{3,}(.*)"

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        if self.pattern is None:
            Exception("Not implemented")
        cmd = ''
        try:
            cmd = self.build_cmd(path)
        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"scanner - Exception occured while scanning: {e}, path: {path}")
            print(f"Scan cmd: {cmd}")
            # pass

        try:
            output = check_output(cmd)
        except CalledProcessError as e:
            output = e.output

        matches = re.findall(self.pattern, output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            self.results[match[self.file_index].strip()] = match[self.malware_index]
        return len(self.results) > 0

# -----------------------------------------------------------------------


class CKasperskyScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Kaspersky"
        # Considered fast because it requires the daemon to be running.
        # This is why...
        self.speed = AV_SPEED_FAST
        self.pattern = r"\d+-\d+-\d+ \d+:\d+:\d+\W(.*)\Wdetected\W(.*)"
        self.pattern2 = '(.*)(INFECTED|SUSPICION UDS:|SUSPICION HEUR:|WARNING HEUR:)(.*)'

    def version(self):
        result = "not implemented"
        return result

    def build_cmd(self, path):
        parser = self.cfg_parser
        scan_path = parser.get(self.name, "PATH")
        scan_args = parser.get(self.name, "ARGUMENTS")
        args = [scan_path]
        ver = os.path.basename(scan_path)
        if ver == "kavscanner":
            args.extend(scan_args.split(" "))
            args.append(path)
        elif ver == "kav":
            args.extend(scan_args.replace("$FILE", path).split(" "))
        return args

    def scan(self, path):
        if self.pattern is None:
            Exception("Not implemented")
        cmd = ''
        try:
            cmd = self.build_cmd(path)
        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"scanner - Exception occured while scanning: {e}, path: {path}")
            print(f"Scan cmd: {cmd}")
            # pass

        try:  # stderr=devnull because kavscanner writes socket info
            with open(os.devnull, "w") as devnull:
                output = check_output(cmd, stderr=devnull)

        except CalledProcessError as e:
            output = e.output
        ver = os.path.basename(cmd.pop(0))
        if ver == "kavscanner":
            self.file_index = 0
            self.malware_index = 2
            matches = re.findall(self.pattern2, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                self.results[match[self.file_index].split('\x08')[0].rstrip()] =\
                    match[self.malware_index].lstrip().rstrip()
        elif ver == "kav":
            matches = re.findall(self.pattern, output, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                self.results[match[self.file_index]] = match[self.malware_index]

        return len(self.results) > 0

# -----------------------------------------------------------------------


class CClamScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "ClamAV"
        self.speed = AV_SPEED_ULTRA

    def version(self):
        try:
            parser = self.cfg_parser
            ep = parser.get(self.name, "UNIX_SOCKET")

            pyclamd.init_unix_socket(filename=ep)
            result = pyclamd.version()
            result = result.replace("ClamAV", "ClamAV Engine version:", 1)
            result = result.replace("/", " ClamAV Dat set version: ", 1) 
            result = result.replace("/", " created ", 1) 
            # print(f"ClamAV version: {result}")
            return result
        except Exception as e:
            print(f"Exception occured while getting Clamav version {e}")

    def scan_one(self, path):
        sys.stdout = open('/var/log/my_script.log', 'a')
        try:
            tmp = pyclamd.scan_file(path)
            if tmp:
                val = list(tmp.values())[0]
                if "Can't create temporary file" in val[1] or "Error" in val[1]:
                    raise Exception(val[1])
                self.results.update(tmp)
            else:
                self.results[path] = None
        except Exception as e:
            print(f"Clamav scanner - Exception occured while scanning {e}, path: {path} RUNNING WITH CLAMSCAN FOR SINGLE FILE")
            try:
                output = subprocess.check_output(['clamscan', '-r', '--scan-archive=yes', '--max-filesize=0', '--max-scansize=0', '--max-recursion=50', '--database=/var/lib/clamav', path], stderr=subprocess.STDOUT, text=True)
                if 'FOUND' in output:
                    virus = output.split(':')[-1].strip()
                    self.results[path] = ('FOUND', virus)
                else:
                    self.results[path] = None
            except subprocess.CalledProcessError as ce:
                print(f'clamscan failed: {ce}')
                self.results[path] = f'clamscan error: {str(ce)}'
            # pass

    def scan_multi(self, path):
        instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id")
        sys.stdout = open('/var/log/my_script.log', 'a')
        failed_files = []

        try:
            tmp = pyclamd.multiscan_file(path)
            if tmp:
                for fpath, result in tmp.items():
                    if "Can't create temporary file" in result[1] or "Error" in result[1]:
                        print(f"[FALLBACK] clamd failed on {fpath}")
                        failed_files.append(fpath)
                    else:
                        self.results.update(tmp)
            else:
                file_count = sum(len(files) for _, _, files in os.walk(path))
                print(f"[{datetime.now()}] - {instance_id.text} - clamd returned no results for {path} — scanned {file_count} file(s)")
                #            print(f"[INFO] clamd returned no results for {path}")
                #failed_files = [os.path.join(root, f) for root, _, files in os.walk(path) for f in files]
                self.results[path] = None
               # Count how many files were scanned by clamd (based on directory listing)
               # file_count = sum(len(files) for _, _, files in os.walk(path))
               # print(f"[{datetime.now()}] [INFO] clamd returned no results for {path} — scanned {file_count} file(s)")
                #print(f"[INFO] clamd returned no results for {path}")
                #failed_files = [os.path.join(root, f) for root, _, files in os.walk(path) for f in files]
                self.results[path] = None
        except Exception as e:
            print(f"[EXCEPTION] clamdscan raised error on {path}: {e}")
            failed_files = [os.path.join(root, f) for root, _, files in os.walk(path) for f in files]

        # Fallback to clamscan for failed files
        if failed_files:
            print(f"[INFO] Running clamscan on {len(failed_files)} fallback files...")
            try:
                cmd = [
                    'clamscan', '-r', '--scan-archive=yes',
                    '--max-filesize=0', '--max-scansize=0', '--max-recursion=50',
                    '--database=/var/lib/clamav'
                ] + failed_files
                output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                print(output)

                for line in output.splitlines():
                    if 'FOUND' in line:
                        parts = line.split(':')
                        file_path = parts[0].strip()
                        virus = parts[-1].strip()
                        self.results[file_path] = ('FOUND', virus)
                    elif ':' in line:
                        file_path = line.split(':')[0].strip()
                        self.results[file_path] = None
            except subprocess.CalledProcessError as ce:
                print(f"[ERROR] clamscan failed: {ce}")
                if hasattr(ce, 'output'):
                    for line in ce.output.splitlines():
                        if 'FOUND' in line:
                            parts = line.split(':')
                            file_path = parts[0].strip()
                            virus = parts[-1].strip()
                            self.results[file_path] = ('FOUND', virus)
                        elif ':' in line:
                            file_path = line.split(':')[0].strip()
                            self.results[file_path] = None

    def scan_dir(self, path):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                self.scan_one(os.path.join(root, name))
        return len(self.results)

    def scan(self, path):
        parser = self.cfg_parser
        ep = parser.get(self.name, "UNIX_SOCKET")

        pyclamd.init_unix_socket(filename=ep)
        if os.path.isdir(path):
            # self.scan_dir(path)
            self.scan_multi(path)
        else:
            self.scan_one(path)
            if not self.results:
                self.results[path] = 'OK'
        return len(self.results) == 0

# -----------------------------------------------------------------------


class CFProtScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "F-Prot"
        self.speed = AV_SPEED_ULTRA
        self.pattern = "\<(.*)\>\s+(.*)"
        self.file_index = 1
        self.malware_index = 0

    def version(self):
        result = "not implemented"
        return result

# -----------------------------------------------------------------------


class CAviraScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Avira"
        self.speed = AV_SPEED_SLOW
        self.pattern = "ALERT: \[(.*)\] (.*) \<\<\<"
        self.file_index = 1
        self.malware_index = 0

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        os.putenv("LANG", "C")
        return CAvScanner.scan(self, path)

# -----------------------------------------------------------------------


class CBitDefenderScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "BitDefender"
        self.speed = AV_SPEED_SLOW
        self.pattern = "(.*) \s+infected:\s(.*)"

    def scan(self, path):
        os.putenv("LANG", "C")
        return CAvScanner.scan(self, path)

# -----------------------------------------------------------------------


class CEsetScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "ESET"
        self.speed = AV_SPEED_MEDIUM

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        os.putenv("LANG", "C")
        cmd = self.build_cmd(path)
        try:
            output = check_output(cmd)
        except CalledProcessError as e:
            output = e.output

        pattern = 'name="(.*)", threat="(.*)",'
        matches = re.findall(pattern, output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            malware = match[1][:match[1].find('", ')]
            if malware != "":
                self.results[match[0]] = match[1][:match[1].find('", ')]
        return len(self.results) > 0

# -----------------------------------------------------------------------


class CSophosScanner(CAvScanner):
    SOPHOS_AVSCANNER = "/opt/sophos-spl/plugins/av/bin/avscanner"
    SOPHOS_TD_LOG = "/opt/sophos-spl/plugins/av/log/sophos_threat_detector/sophos_threat_detector.log"
    sophos_log = "/var/log/sophos/sophos-scan-${EC2_ID}.log" 

    # error signals to treat as scan failure
    _ERROR_PATTERNS = [
        r"Failed to scan",
        r"Failed to send scan request",
        r"Failed to scan one or more files due to an error",
        r"scan error encountered",
        r"after \d+ retries",
    ]

    def _read_log_delta(self, start_pos: int) -> str:
        try:
            with open(self.sophos_log, "r", encoding="utf-8", errors="replace") as f:
                f.seek(start_pos)
                return f.read()
        except FileNotFoundError:
            return ""
        except PermissionError:
            return ""

    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Sophos"
   #     self.speed = AV_SPEED_MEDIUM
   #     self.pattern = "Virus '(.*)' found in file (.*)"
        self.pattern = re.compile(r"Virus '([^']+)' found in file (.+)")
        self.file_index = 1
        self.malware_index = 0

    # ----- versions() support -------------------------------------------------
    def _read_tail(self, file_path: str, max_bytes: int = 1_500_000) -> str:
        """Read up to the last max_bytes from a (potentially large) log file."""
        p = Path(file_path)
        if not p.exists():
            return ""
        size = p.stat().st_size
        with p.open("rb") as f:
            if size > max_bytes:
                f.seek(size - max_bytes)
                # discard partial first line
                f.readline()
            return f.read().decode(errors="ignore")

    def _versions_from_log(self) -> dict:
        SOPHOS_AVSCANNER = "/opt/sophos-spl/plugins/av/bin/avscanner"
        SOPHOS_TD_LOG = "/opt/sophos-spl/plugins/av/log/sophos_threat_detector/sophos_threat_detector.log"
        """
        Pull AV plugin (product), SAVI engine, and VDB/defs from detector log.
        Looks for lines present in your log:
          - JSON with "product": {"name":"SUSI_SPLAV","version":"X.Y.Z"}
          - 'SAVI: ... (3.93.1)'  -> engine
          - 'VDB manifest version: 2025091107' -> defs
        """
        info = {}
        text = self._read_tail(SOPHOS_TD_LOG)

        # AV plugin version (product SUSI_SPLAV) – appears in a JSON blob
        m = re.search(r'"product"\s*:\s*\{[^}]*"name"\s*:\s*"SUSI_SPLAV"[^}]*"version"\s*:\s*"([0-9.]+)"', text)
        if m:
            info["av_plugin_version"] = m.group(1)

        # SAVI engine (e.g., 'SAVI: ... (3.93.1)')
        m = re.search(r'SAVI:[^\(]*\(([0-9.]+)\)', text)
        if m:
            info["engine_version"] = m.group(1)

        # VDB manifest version (defs), e.g. 'VDB manifest version: 2025091107'
        m = re.search(r'VDB manifest version:\s*([0-9]+)', text)
        if m:
            info["data_version"] = m.group(1)

        return info

    def version(self) -> str:
        v = self._versions_from_log()
        parts = []
        if v.get("av_plugin_version"):
            parts.append(f"Sophos AV Plugin Version: {v['av_plugin_version']}")
        if v.get("engine_version"):
            parts.append(f"Sophos Engine: {v['engine_version']}")
        if v.get("data_version"):
            parts.append(f"Sophos Data Defs: {v['data_version']}")
        return " ".join(parts) if parts else "Sophos SPL (version info unavailable)"

    def _read_related_logs(self, base_log: str, scan_started_epoch: float) -> str:
        # includes base + rotated/split logs like .1 .2 or timestamped suffixes
        candidates = [Path(p) for p in glob(base_log + "*")]

        # keep only logs updated during/after scan start
        candidates = [p for p in candidates if p.exists() and p.stat().st_mtime >= scan_started_epoch]

        # read oldest->newest so parsing makes sense
        candidates.sort(key=lambda p: p.stat().st_mtime)

        chunks = []
        for p in candidates:
            try:
                chunks.append(p.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                continue

        return "\n".join(chunks)

    
    def _is_infected_value(self, v) -> bool:
        # v is either "OK", "<signature>", ("ERROR", "<snippet>"), or None
        if isinstance(v, tuple):  # errors aren't infections
            return False
        if v is None:
            return False
        return str(v).upper() != "OK"


        #Rollup normalized detections to the top file so files will be marked INFECTED
    def rollup_to_scanned_path(self, results: dict, scanned_path: str) -> None:
        if not results:
            return

        # Do NOT bail just because scanned_path exists; it may be "OK"
        #if scanned_path in results and self._is_infected_value(results[scanned_path]):
        #    return

        scanned_real = os.path.realpath(scanned_path).rstrip(os.sep)
        prefix_real = scanned_real + os.sep

        infected_sigs = []
        for fp, sig in results.items():
            if not self._is_infected_value(sig):
                continue

            fp_real = os.path.realpath(fp).rstrip(os.sep)

            # Your exact case: inner path begins with scanned_path + "/"
            if fp_real.startswith(prefix_real):
                infected_sigs.append(str(sig))

        if infected_sigs:
            # dedupe keep order
            uniq = []
            for s in infected_sigs:
                if s not in uniq:
                    uniq.append(s)

            # This is the key: mark the TOP-LEVEL scanned object infected
        try:
            for outer in Path(scanned_path).rglob("*"):
                if not outer.is_file():
                    continue
                outer_str = str(outer)

                prefix = outer_str.rstrip(os.sep) + os.sep
                sigs = []
                
                for fp, sig in results.items():
                    if fp.startswith(prefix) and sig and str(sig).upper() != "OK" and not isinstance(sig, tuple):
                        sigs.append(sig)

                if sigs:
                    results[outer_str] = sigs[0]   # <- list of signatures
        except Exception:
            pass

    #record detections and infections
    #Setting up a way to manually write to custom log rather
    #than using Sophos logging.
    def _run_and_capture(self, cmd: list[str], full_log: str, detect_log: str, error_log: str):
        """
        Runs avscanner, writes full output to full_log,
        writes only detection lines to detect_log,
        and returns (exit_code, detections_list).

        detections_list format:
            [
                {"path": "/path/to/file", "sig": "EICAR-AV-Test"},
                ...
            ]
        """

        # Detection patterns (support multiple Sophos formats)
        DETECTION_PATTERNS = [
            # Detected "/path/file" is infected with SIGNATURE
            re.compile(
                r'Detected\s+"(?P<path>[^"]+)"\s+is infected with\s+(?P<sig>.+?)(?:\s+\(On Demand\))?\s*$',
                re.IGNORECASE,
            ),

            # Virus 'SIGNATURE' found in file /path/file
            re.compile(
                r"Virus\s+'(?P<sig>[^']+)'\s+found in file\s+(?P<path>.+)$",
                re.IGNORECASE,
            ),
        ]

        ERROR_PATTERNS = [
                re.compile(
                    r'ERROR Failed to scan\s+(?P<path>.+?)\s+as it is\s+(?P<reason>password protected)\s*$',
                    re.IGNORECASE,
                ),
                re.compile(
                    r'ERROR Failed to get the symlink status of\:\s+(?P<path>.+?)\s+\[(?P<reason>permission denied)\]\s*$',
                    re.IGNORECASE,
                ),
                re.compile(
                    r'ERROR Failed to scan\s+(?P<path>.+?)\s+as it is\s+(?P<reason>corrupted)\s*$',
                    re.IGNORECASE,
                ),
                re.compile(
                    r'ERROR Failed to send scan\s+(?P<path>.+?)\s*$',
                    re.IGNORECASE
                ),
                re.compile(
                    r'Failed to send scan request',
                    re.IGNORECASE
                ),
               # re.compile(r"scan error encountered", re.IGNORECASE),
                re.compile(
                    r'after \d+ retries',
                    re.IGNORECASE
                ),
            ]
        Path(full_log).parent.mkdir(parents=True, exist_ok=True)
        errors = []
        detections = []
        det_fp = None
        error_fp = None

        # Ensure directories exist
        try: 
            with subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # line buffered
                universal_newlines=True,
            ) as proc, \
                    open(full_log, "a", encoding="utf-8") as full_fp:

                for line in proc.stdout:
                    # Write everything to main scan log
                    full_fp.write(line)
                    full_fp.flush()

                    stripped = line.strip()

                    for rx in ERROR_PATTERNS:
                        match = rx.search(stripped)
                        if match:
                            ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                            fpath = (match.groupdict().get("path") or path).strip()
                            reason = match.groupdict().get("reason") or "ERROR"
                            if error_fp is None:
                                error_fp = open(error_log, "a", encoding="utf-8")

                            error_fp.write(f"{ts} path={fpath} reason={reason}\n")
                            error_fp.flush()

                            errors.append({
                                "path": fpath,
                                "reason": reason,
                            })
                            break  # stop checking other patterns
                    # Check for detection lines
                    for rx in DETECTION_PATTERNS:
                        match = rx.search(stripped)
                        if match:
                            ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                            fpath = match.group("path").strip()
                            sig = match.group("sig").strip()
                            if det_fp is None:
                                det_fp = open(detect_log, "a", encoding="utf-8")

                            det_fp.write(f"{ts} path={fpath} sig={sig}\n")
                            det_fp.flush()

                            detections.append({
                                "path": fpath,
                                "sig": sig,
                            })
                            break  # stop checking other patterns

                exit_code = proc.wait()

            return exit_code, detections, errors
        finally:
            if det_fp is not None:
                det_fp.close()
            if error_fp is not None:
                error_fp.close()

        # ----- scanning -----------------------------------------------------------
    def scan(self, path: str):
        os.putenv("LANG", "C")
        ec2_id = os.environ.get("EC2_ID")
        if not ec2_id:
            raise RuntimeError("EC2_ID not set")

        self.sophos_log = f"/var/log/sophos/sophos-scan-{ec2_id}.log"
        scan_started = time.time()
        scan_id = f"{ec2_id}-{int(time.time())}"
        full_log = f"/var/log/sophos/{ec2_id}/sophos-scan-{ec2_id}.log"
        detect_log = f"/var/log/sophos/detections/sophos-detections-{scan_id}.log"
        error_log = f"/var/log/sophos/errors/sophos-errors-{scan_id}.log"

        cmd = [
            self.SOPHOS_AVSCANNER,
            "--scan-archives",
            "--scan-images",
            "--follow-symlinks",
            path,
        ]

       # rc, detections, errors = self._run_and_capture(cmd, full_log, detect_log, error_log)
        # IMPORTANT: MultiAV reads av.results, so set self.results
#
        try:
            start_pos = os.path.getsize(self.sophos_log)
        except OSError:
            start_pos = 0
        """
        Return per-file results for Multi-AV:
          OK  -> clean
          <signature> -> detected
          ('ERROR', '<message>') -> scanner error
        """
        
        rc, detections, errors = self._run_and_capture(cmd, full_log, detect_log, error_log)
        self.results = {}
        try:
            rc, detections, errors = self._run_and_capture(cmd, full_log, detect_log, error_log)

            if path not in self.results:
            # Sometimes Sophos logs the same path but normalized; match by suffix as a backup
                for fp, sig in self.results.items():
                    self.rollup_to_scanned_path(self.results, path)
                    if fp.startswith(path + os.sep):
                        self.results[path] = sig
                        break
#
        except Exception as e:
            self.results[path] = ("ERROR", str(e))
        finally:
            # self.pattern = old_pattern
            for outer in Path(path).rglob("*"):
                try:
                    if not outer.is_file():
                        continue
                except PermissionError as e:
                    self.results[str(outer)] = ("ERROR", str(e))
                outer_str = str(outer)
                prefix = outer_str.rstrip(os.sep) + os.sep
             #   print(f"{bcolors.DEBUG}****This is the value of outer_str {outer_str} {bcolors.ENDC}")
                log_delta = self._read_log_delta(start_pos) or ""
                det_pattern = re.compile(
                    r'Detected\s+"([^"]+)"\s+is infected with\s+(.+?)(?:\s+\(On Demand\))?\s*$',
                    re.IGNORECASE | re.MULTILINE,
                )
                error_pattern = re.compile(
                        r'ERROR Failed to scan\s+(.+?)\s+as it is \s+(.+?)\s*$',
                        re.IGNORECASE | re.MULTILINE,
                )
                
                if rc != 0 and any(str(e.get("path", "")).startswith(outer_str) for e in detections if isinstance(e, dict)):
                    self.results[outer_str] = detections[0]["sig"]
                    print(f"{bcolors.WARNING} INFECTION  IN  OBJECT: {self.results}{bcolors.ENDC}")
                  #  return self.results
                elif rc != 0 and any(str(e.get("path", "")).startswith(outer_str) for e in errors if isinstance(e, dict)):
                    # mark outer object infected using first signature
                    err = next(
                        (e for e in errors if isinstance(e, dict) and str(e.get("path", "")).startswith(outer_str)),
                        None
                    )
                    reason = err.get("reason", "ERROR") if err else "ERROR"
                    self.results[outer_str] = ("ERROR", "Failed scan due to being "+reason)
                    print(f"{bcolors.FAIL} ERROR IN  OBJECT: {self.results}{bcolors.ENDC}")
                    #return self.results
                else:
                    self.results[path] = "OK"
                
            print(f"{bcolors.DEBUG} RESULTS IN  OBJECT: {self.results}{bcolors.ENDC}")


            return self.results

# -----------------------------------------------------------------------


class CAvastScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Avast"
        self.speed = AV_SPEED_ULTRA
        self.pattern = "(.*)\t(.*)"

    def scan(self, path):
        os.putenv("LANG", "C")
        return CAvScanner.scan(self, path)

    def version(self):
        result = "not implemented"
        return result

# -----------------------------------------------------------------------


class CDrWebScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "DrWeb"
        self.speed = AV_SPEED_SLOW
        self.pattern = "\>{0,1}(.*) infected with (.*)"

    def version(self):
        result = "not implemented"
        return result

# -----------------------------------------------------------------------


class CEScanScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "MicroWorld-eScan"
        self.speed = AV_SPEED_FAST
        self.pattern = '(.*)\[INFECTED\](.*)'

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        if self.pattern is None:
            Exception("Not implemented")

        cmd = ''
        try:
            cmd = self.build_cmd(path)
        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"Scan cmd: {cmd}")
            print(f"CAvScanner scanner - Exception occured while scanning {e}, path: {path}")
            # pass

        try:
            output = check_output(cmd)
        except CalledProcessError as e:
            output = e.output

        matches = re.findall(self.pattern, output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            self.results[match[self.file_index].rstrip()] = match[self.malware_index]
        return len(self.results) > 0

# -----------------------------------------------------------------------


class CMcAfeeScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        print("Initializing McAfee")
        self.name = "McAfee"
        self.speed = AV_SPEED_FAST
        # self.pattern = "(.*) \.\.\. Found[:| the]{0,1} (.*) [a-z]+ [\!\!]{0,1}"
        self.pattern = "(.*) \.\.\. Found:{0,1} (.*) [a-z]+ [\!\!]{0,1}"
        # self.pattern2 = "(.*) \.\.\. Found [a-z]+ or variant (.*) \!\!"

    def version(self):
        version = ""
        engine = ""
        dat = ""
        result = CAvScanner.version(self)
        for line in result.split("\n"):
            if "AV Engine version" in line:
                print(f"engine: {line}")
                engine = "McAfee " + line
            elif "Dat set version" in line:
                print(f"dat: {line}")
                dat = " McAfee " + line
            else:
                continue
        version = engine + dat
        return version

    def scan(self, path):
        instance_id = requests.get("http://169.254.169.254/latest/meta-data/instance-id")
        sys.stdout = open('/var/log/my_script.log', 'a')
        try:
            # os.putenv("LANG", "C")
            # ret = CAvScanner.scan(self, path)
            # old_pattern = self.pattern
            # self.pattern = self.pattern2
            ret = CAvScanner.scan(self, path)
        finally:
            # self.pattern = old_pattern
            print(f"McAfee completed scan Results: {self.results}")
            if not self.results:
                self.results[path] = 'OK'
            # print(f"scan ret after try: {ret}")

        for match in self.results:
            # print(f"McAfee scan match: %s " % (match))
            self.results[match] = self.results[match].strip("the ")
        self.results[match] = self.results[match].split()[0]
        print(f"McAfee scan match for: {match} Return results: %s " % (self.results[match]))
        print(f"[{datetime.now()}] - {instance_id.text} McAfee scanned {len(self.results)} files")
        return ret

# -----------------------------------------------------------------------


class CAvgScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "AVG"
        # Considered fast because it requires the daemon to be running.
        # This is why...
        self.speed = AV_SPEED_ULTRA
        self.pattern1 = "\>{0,1}(.*) \s+[a-z]+\s+[a-z]+\s+(.*)"
        self.pattern2 = "\>{0,1}(.*) \s+[a-z]+\s+(.*)"  # like this:Luhe.Fiha.A

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        cmd = self.build_cmd(path)
        f = NamedTemporaryFile(delete=False)
        f.close()
        fname = f.name

        try:
            cmd.append("-r%s" % fname)
            output = check_output(cmd)
        except CalledProcessError as e:
            output = e.output

        output = open(fname, "rb").read()
        os.unlink(fname)

        matches1 = re.findall(self.pattern1, output, re.IGNORECASE | re.MULTILINE)
        matches2 = re.findall(self.pattern2, output, re.IGNORECASE | re.MULTILINE)
        matches = matches1 + matches2
        for match in matches:
            if match[1] not in ["file"]:
                self.results[match[0].split(':/')[0]] = match[1]
        return len(self.results) > 0

# -----------------------------------------------------------------------


class CIkarusScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "Ikarus"
        self.speed = AV_SPEED_MEDIUM
        # Horrible, isn't it?
        self.pattern = "(.*) - Signature \d+ '(.*)' found"

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        cmd = self.build_cmd(path)
        f = NamedTemporaryFile(delete=False)
        f.close()
        fname = f.name

        try:
            cmd.append("-logfile")
            cmd.append(fname)
            output = check_output(cmd)
        except CalledProcessError as e:
            output = e.output

        output = codecs.open(fname, "r", "utf-16").read()
        os.unlink(fname)

        matches = re.findall(self.pattern, output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            if match[1] not in ["file"]:
                self.results[match[0]] = match[1]
        return len(self.results) > 0

# -----------------------------------------------------------------------


class CFSecureScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "F-Secure"
        self.speed = AV_SPEED_FAST
        self.pattern = "(.*): Infected: (.*) \[[a-z]+\]"

    def version(self):
        result = "not implemented"
        return result

# -----------------------------------------------------------------------


class CQuickHealScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.cfg_parser = cfg_parser
        self.name = 'QuickHeal'
        self.speed = AV_SPEED_FAST
        self.file_index = 1
        self.malware_index = 2
        self.pattern = '(Scanning : |Archive  : )(.*)\nInfected[\s]+:[\s]+\((.*)\)'

    def build_cmd(self, path):
        parser = self.cfg_parser
        scan_path = parser.get(self.name, "PATH")
        scan_args = parser.get(self.name, "ARGUMENTS")
        args = [scan_path]
        args.extend(scan_args.replace("$FILE", path).split(" "))
        return args

    def version(self):
        result = "not implemented"
        return result

    def scan(self, path):
        f = NamedTemporaryFile(delete=False)
        f.close()
        fname = f.name

        if self.pattern is None:
            Exception("Not implemented")

        cmd = ''
        try:
            cmd = self.build_cmd(path)

        except Exception as e:  # There is no entry in the *.cfg file for this AV engine?
            print(f"scanner - Exception occured while scanning: {e}, path: {path}")
            print(f"Scan cmd: {cmd}")
            # pass

        try:
            # cmd.append("-REPORT=%s" % fname)
            cmd += ("-REPORT=%s" % fname)
            output = check_output(cmd)

        except CalledProcessError as e:
            output = e.output

        output = open(fname, "rb").read()
        os.unlink(fname)
        matches = re.findall(self.pattern, output, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            self.results[match[self.file_index].rstrip('\r')] = match[self.malware_index]

        return len(self.results) > 0

# -----------------------------------------------------------------------


class CZavScanner(CAvScanner):
    def __init__(self, cfg_parser):
        CAvScanner.__init__(self, cfg_parser)
        self.name = "ZAV"
        self.speed = AV_SPEED_ULTRA
        self.pattern = "(.*): INFECTED \[(.*)\]"

# -----------------------------------------------------------------------


class CMultiAV:
    def __init__(self, cfg="/app/scanners/functions/config.cfg"):
        print("[DEBUG] Config file path %s" % cfg)
        self.engines = [CFProtScanner,  CComodoScanner,      CEsetScanner,
                        CAviraScanner,  CBitDefenderScanner, CSophosScanner,
                        CAvastScanner,  CAvgScanner,         CDrWebScanner,
                        CMcAfeeScanner, CIkarusScanner,      CFSecureScanner,
                        CKasperskyScanner, CZavScanner,      CEScanScanner,
                        CCyrenScanner,  CQuickHealScanner,   CTrendmicroScanner]
        if has_clamd:
            self.engines.insert(0, CClamScanner)

        self.processes = cpu_count()
        self.cfg = cfg
        self.read_config()

    def read_config(self):
        parser = ConfigParser()
        parser.optionxform = str
        parser.read(self.cfg)
        self.parser = parser

    def multi_scan(self, path, max_speed):
        q = Queue()
        engines = list(self.engines)
        running = []
        results = {}

        while len(engines) > 0 or len(running) > 0:
            if len(engines) > 0 and len(running) < self.processes:
                av_engine = engines.pop()
                # print(f"Trying to scan using engine: %s" % av_engine)
                args = (av_engine, path, results, max_speed, q)
                p = Process(target=self.scan_one, args=args)
                p.start()
                running.append(p)

            newrunning = []
            for p in list(running):
                p.join(0.1)
                if p.is_alive():
                    newrunning.append(p)
            running = newrunning

        results = {}
        while not q.empty():
            results.update(q.get())
        print(f"multi_scan returns results: {results}")
        return results

    def scan(self, path, max_speed=AV_SPEED_ALL):
        if not os.path.exists(path):
            raise Exception("Path not found")

        if self.processes > 1:
            return self.multi_scan(path, max_speed)
        else:
            return self.single_scan(path, max_speed)

    def single_scan(self, path, max_speed=AV_SPEED_ALL):
        results = {}
        for av_engine in self.engines:
            results = self.scan_one(av_engine, path, results, max_speed)
        return results

    def versions(self, q=None):
        results = {}
        for av_engine in self.engines:
            av = av_engine(self.parser)
            if av.is_disabled():
                continue
            results[av.name] = av.version()
            # print(f"Scanner: {av.name}, Version: {results[av.name]}")
        if q is not None:
            q.put(results)
        return results

    def scan_one(self, av_engine, path, results, max_speed, q=None):
        av = av_engine(self.parser)
        # print('[DEBUG] Engine: {:20} State: {:8} File Path: {:60}'.format(av.name, "DISABLED" if av.is_disabled() else "ENABLED", path))
        if av.is_disabled():
            return results

        if av.speed <= max_speed:
            # print(f"scan_one: av_engine: {av_engine} path; {path} results: {results} max_speed: {max_speed}")
            av.scan(path)
            results[av.name] = av.results

        if q is not None:
            q.put(results)
        return results

    def scan_buffer(self, buf, max_speed=AV_SPEED_ALL):
        f = NamedTemporaryFile(delete=False)
        f.write(buf)
        f.close()

        fname = f.name
        os.chmod(f.name, 436)

        try:
            ret = self.scan(fname, max_speed)
        finally:
            os.unlink(fname)

        return ret
