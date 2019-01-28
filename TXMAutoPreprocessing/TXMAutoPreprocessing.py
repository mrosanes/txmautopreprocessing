import sys
import subprocess
import pprint

from taurus.core.util.threadpool import ThreadPool
from taurus.core.util.enumeration import Enumeration

from PyTango import AttrWriteType, DevState, DebugIt, AttReqType
from PyTango.server import Device, DeviceMeta, attribute, run, command


Action = Enumeration(
    'Action', (
        'PIPELINE',
        'THETA',
        'ID',
        'ENERGY',
        'END'
    ))

Pipeline = Enumeration(
    'Pipeline', (
        'MAGNETISM',
        'TOMO',
        'SPECTRO'
    ))


class TXMAutoPreprocessing(Device):
    __metaclass__ = DeviceMeta

    Select = attribute(label="Select", dtype=float,
                       access=AttrWriteType.READ_WRITE,
                       fget="get_Select", fset="set_Select",
                       doc="action select")

    Target = attribute(label="Target", dtype=float,
                       access=AttrWriteType.READ_WRITE,
                       fget="get_Target", fset="set_Target",
                       doc="action target")

    TXM_file = attribute(label="TXM_file", dtype=str,
                         access=AttrWriteType.READ_WRITE,
                         fget="get_TXM_file", fset="set_TXM_file",
                         doc="txm file")

    HOST = "pcbl0903"
    USER = "opbl09"

    def init_device(self):
        Device.init_device(self)
        self._select = float("NaN")
        self._target = float("NaN")
        self._txm_file = None
        self._command = None
        self._pipeline = None
        self.set_state(DevState.STANDBY)
        self.user_host = '{0}@{1}'.format(self.USER, self.HOST)
        self._thread_pool = ThreadPool(name="Preprocessing",
                                       parent=None,
                                       Psize=1,
                                       Qsize=0)
        self._count_command = 1

    @DebugIt(show_args=True)
    def set_TXM_file(self, txmfile):
        self.debug_stream("Set TXM_file: %s" % (txmfile))
        self._txm_file = txmfile

    def get_TXM_file(self):
        return self._txm_file

    def is_TXM_file_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() in [DevState.STANDBY]

    @DebugIt(show_args=True)
    def set_Select(self, select):
        self.debug_stream("Set select: %s" % (select))
        self._select = select

    def get_Select(self):
        return self._select

    def is_Select_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() not in [DevState.STANDBY]

    @DebugIt(show_args=True)
    def set_Target(self, target):
        print("setting target")
        self._target = target
        self.debug_stream("Set target: %s" % (target))
        if self._select == Action.PIPELINE:
            if target == Pipeline.MAGNETISM:
                print("hiho magnetism")
                self._command = "magnetism {0} {1}"
                self._pipeline = Pipeline.MAGNETISM
                args = '--db --ff'
            elif target == Pipeline.TOMO:
                print("Beginning of Tomo pipeline")
                # eg: ctbiopartial test.txt --db
                # eg: ctbiopartial test.txt --id=1
                # (id of first xrm record for each sample)
                self._command = "ctbiopartial {0} {1}"
                self._pipeline = Pipeline.TOMO
                args = '--db'
        elif self._select == Action.THETA:
            args = '--th {0}'.format(self._target)
        elif self._select == Action.ID and self._pipeline == Pipeline.TOMO:
            args = '--id {0}'.format(self._target)
        if self._select != Action.END:
            print(self._txm_file)
            print(args)
            command = self._command.format(self._txm_file, args)
            self.debug_stream("command %s" % (command))
            print(command)
            self._thread_pool.add(self.run_command, None, command)
        else:
            self._thread_pool.add(self.end, None)

    def get_Target(self):
        return self._target

    def is_Target_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() not in [DevState.STANDBY]

    @DebugIt(show_args=True)
    def run_command(self, command, state=DevState.ON):
        #print("begin execute command")
        #print(self._count_command)
        self.debug_stream("run_command %s" % (command))
        self.set_state(DevState.RUNNING)
        ssh = subprocess.Popen(["ssh", '-t', self.user_host, command],
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        out, err = ssh.communicate()
        if out is not None or len(out) != 0:
            self.debug_stream(out.replace('%', '%%'))
        #print("state ON")
        self.set_state(state)
        #print(self._count_command)
        #print("end execute command")
        self._count_command += 1

    def delete_device(self):
        self._thread_pool.join()
        self._thread_pool = None

    @command()
    @DebugIt()
    def start(self):
        self.set_state(DevState.ON)

    def is_start_allowed(self):
        return self.get_state() in [DevState.STANDBY]

    @command()
    @DebugIt()
    def end(self):
        if self._pipeline == Pipeline.MAGNETISM:
            args = '--stack'
            command = self._command.format(self._txm_file, args)
            self.debug_stream("run_command %s" % (command))
            self._thread_pool.add(self.run_command, None, command,
                                  DevState.STANDBY)
        elif self._pipeline == Pipeline.TOMO:
            self._thread_pool.add(self.set_state, None, DevState.STANDBY)
            print("End of tomo pipeline: setting DS state to standby")

    def is_end_allowed(self):
        return self.get_state() in [DevState.ON]

    @command()
    def stop(self):
        self.init_device()


def runDS():
    run([TXMAutoPreprocessing])


if __name__ == "__main__":
    runDS()

