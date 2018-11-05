import sys
import subprocess
import pprint

from taurus.core.util.threadpool import ThreadPool
# from enum import IntEnum
from taurus.core.util.enumeration import Enumeration


from PyTango import AttrWriteType, DevState, DebugIt, AttReqType
from PyTango.server import Device, DeviceMeta, attribute, run, command


# class Action(IntEnum):
#     PIPELINE = 0
#     THETA = 1
#     ENERGY = 2
#
# class Pipeline(IntEnum):
#     MAGNETISM = 0
#     TOMO = 1
#     SPECTRO = 2

Action = Enumeration(
    'Action', (
        'PIPELINE',
        'THETA',
        'ENERGY'
    ))

Pipeline = Enumeration(
    'Pipeline', (
        'MAGNETISM',
        'TOMO'
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
        self._select = None
        self._target = None
        self._txm_file = None
        self._command = None
        self._pipeline = None
        self.set_state(DevState.STANDBY)
        self.user_host = '{0}@{1}'.format(self.USER, self.HOST)
        self._thread_pool = ThreadPool(name="Preprocessing",
                                       parent=None,
                                       Psize=1,
                                       Qsize=0)

    @DebugIt(show_args=True)
    def set_TXM_file(self, txmfile):
        self._txm_file = txmfile

    def get_TXM_file(self):
        return self._txm_file
    
    def is_TXM_file_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() in [DevState.STANDBY]

    def get_Select(self):
        return self._select

    def is_Select_file_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() not in [DevState.STANDBY]
    
    @DebugIt(show_args=True)
    def set_Target(self, target):
        self._target = target
        if self._select == Action.PIPELINE:
            if target == Pipeline.MAGNETISM:
                self._command = "magnetism {0} {1}"

                self._pipeline = Pipeline.MAGNETISM
                args = '--db --ff'
            elif target == Pipeline.TOMO:
                self._command = "TODO"
                self._pipeline = Pipeline.TOMO
        elif self._select == Action.THETA:
            args = '--th {0}'.format(self._target)
        command = self._command.format(self._txm_file, args)
        self._thread_pool.add(self.run_command, None, command)
 
    def run_command(self, command, state=DevState.ON):
        self.set_state(DevState.RUNNING)
        ssh = subprocess.Popen(["ssh", '-t', self.user_host, command],
                               shell=False,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        result = ssh.stdout.readlines()
        if result == []:
            errors = ssh.stderr.readlines()
            print "\n\n", len(errors)
            pprint.pprint(errors, sys.stderr)
            self.set_state(DevState.FAULT)
        else:
            for line in result:
                print line
            self.set_state(state)
    
    def get_Target(self):
        return self._target

    @DebugIt(show_args=True)
    def set_Select(self, select):
        self._select = select

    def is_Target_file_allowed(self, req_type):
        if req_type == AttReqType.READ_REQ:
            return True
        else:
            return self.get_state() not in [DevState.STANDBY]

    def delete_device(self):
        self._thread_pool.join()
        self._thread_pool = None

    @command()
    def start(self):
        self.set_state(DevState.ON)

    def is_start_allowed(self):
        return self.get_state() in [DevState.STANDBY]

    @command()
    def end(self):
        if self._pipeline ==  Pipeline.MAGNETISM:
            args = '--stack'
        command = self._command.format(self._txm_file, args)    
        self._thread_pool.add(self.run_command, None, command,
                              DevState.STANDBY)

    def is_end_allowed(self):
        return self.get_state() in [DevState.ON]
    
    @command()
    def stop(self):
        self.init_device()


def runDS():
    run([TXMAutoPreprocessing])


if __name__ == "__main__":
    runDS()
