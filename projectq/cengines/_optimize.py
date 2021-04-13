#   Copyright 2017 ProjectQ-Framework (www.projectq.ch)
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

"""
Contains a local optimizer engine.
"""
from copy import deepcopy as _deepcopy
from projectq.cengines import LastEngineException, BasicEngine
from projectq.ops import FlushGate, FastForwardingGate, NotMergeable, XGate
from projectq.ops._basics import Commutability


class LocalOptimizer(BasicEngine):
    """
    LocalOptimizer is a compiler engine which optimizes locally (e.g. merging
    rotations, cancelling gates with their inverse) in a local window of user-
    defined size.
    It stores all commands in a dict of lists, where each qubit has its own
    gate pipeline. After adding a gate, it tries to merge / cancel successive
    gates using the get_merged and get_inverse functions of the gate (if
    available). For examples, see BasicRotationGate. Once a list corresponding
    to a qubit contains >=m gates, the pipeline is sent on to the next engine.
    """
    def __init__(self, m=5, apply_commutation=True):
        """
        Initialize a LocalOptimizer object.
        Args:
            m (int): Number of gates to cache per qubit, before sending on the
                first gate.
            apply_commutation (Boolean): Indicates whether to consider commutation
                rules during optimization.
        """
        BasicEngine.__init__(self)
        self._l = dict()  # dict of lists containing operations for each qubit
        self._m = m  # wait for m gates before sending on
        self._apply_commutation = apply_commutation

    def _send_qubit_pipeline(self, idx, n):
        """
        Send n gate operations of the qubit with index idx to the next engine.
        """
        cmd_list = self._l[idx]  # command list for qubit idx
        for i in range(min(n, len(cmd_list))):  # loop over first n commands
            # send all gates before nth gate for other qubits involved
            # --> recursively call send_helper
            other_involved_qubits = [qb
                                     for qreg in cmd_list[i].all_qubits
                                     for qb in qreg
                                     if qb.id != idx]
            for qb in other_involved_qubits:
                Id = qb.id
                try:
                    gateloc = 0
                    # find location of this gate within its list
                    while self._l[Id][gateloc] != cmd_list[i]:
                        gateloc += 1

                    gateloc = self._optimize(Id, gateloc)
                    # flush the gates before the n-qubit gate
                    self._send_qubit_pipeline(Id, gateloc)
                    # delete the nth gate, we're taking care of it
                    # and don't want the other qubit to do so
                    self._l[Id] = self._l[Id][1:]
                except IndexError:
                    print("Invalid qubit pipeline encountered (in the"
                          " process of shutting down?).")

            # all qubits that need to be flushed have been flushed
            # --> send on the n-qubit gate
            self.send([cmd_list[i]])
        # n operations have been sent on --> resize our gate list
        self._l[idx] = self._l[idx][n:]

    def _get_gate_indices(self, idx, i, IDs):
        """
        Return all indices of a command, each index corresponding to the
        command's index in one of the qubits' command lists.
        Args:
            idx (int): qubit index
            i (int): command position in qubit idx's command list
            IDs (list<int>): IDs of all qubits involved in the command
        """
        N = len(IDs)
        # 1-qubit gate: only gate at index i in list #idx is involved
        if N == 1:
            return [i]

        # When the same gate appears multiple time, we need to make sure not to
        # match earlier instances of the gate applied to the same qubits. So we
        # count how many there are, and skip over them when looking in the
        # other lists.
        cmd = self._l[idx][i]
        num_identical_to_skip = sum(1
                                    for prev_cmd in self._l[idx][:i]
                                    if prev_cmd == cmd)
        indices = []
        for Id in IDs:
            identical_indices = [i
                                 for i, c in enumerate(self._l[Id])
                                 if c == cmd]
            indices.append(identical_indices[num_identical_to_skip])
        return indices

    def _delete_command(self, idx, command_idx):
        """ 
        Deletes the command at self._l[idx][command_idx] accounting 
        for all qubits in the optimizer dictionary. 

        Args:
            idx (int): qubit index
            command_idx (int): command position in qubit idx's command list
        """
        # List of the indices of the qubits that are involved
        # in command
        qubitids = [qb.id for sublist in self._l[idx][command_idx].all_qubits
                for qb in sublist]
        # List of the command indices corresponding to the position
        # of this command on each qubit id 
        commandidcs = self._get_gate_indices(idx, command_idx, qubitids)
        for j in range(len(qubitids)):
            try:
                new_list = (self._l[qubitids[j]][0:commandidcs[j]] +
                            self._l[qubitids[j]][commandidcs[j]+1:])
            except IndexError: 
                # If there are no more commands after that being deleted.
                new_list = (self._l[qubitids[j]][0:commandidcs[j]])
            self._l[qubitids[j]] = new_list

    def _replace_command(self, idx, command_idx, new_command):
        """ 
        Replaces the command at self._l[idx][command_idx] accounting 
        for all qubits in the optimizer dictionary. 

        Args:
            idx (int): qubit index
            command_idx (int): command position in qubit idx's command list
            new_command (Command): The command to replace the command 
                at self._l[idx][command_idx]
        """
        # Check that the new command concerns the same qubits as the original 
        # command before starting the replacement process
        assert new_command.all_qubits == self._l[idx][command_idx].all_qubits
        # List of the indices of the qubits that are involved
        # in command
        qubitids = [qb.id for sublist in self._l[idx][command_idx].all_qubits
                for qb in sublist]
        # List of the command indices corresponding to the position
        # of this command on each qubit id 
        commandidcs = self._get_gate_indices(idx, command_idx, qubitids)
        for j in range(len(qubitids)):
            try:
                new_list = (self._l[qubitids[j]][0:commandidcs[j]] 
                            + [new_command]
                            + self._l[qubitids[j]][commandidcs[j]+1:])
            except IndexError: 
                # If there are no more commands after that being replaced.
                new_list = (self._l[qubitids[j]][0:commandidcs[j]] + [new_command])
            self._l[qubitids[j]] = new_list

    def _can_cancel_by_commutation(self, idx, qubitids, commandidcs, inverse_command, apply_commutation):
        """
        Determines whether inverse commands should be cancelled
        with one another. i.e. the commands between the pair are all
        commutable for each qubit involved in the command.

        Args:
            idx (int): qubit index
            qubitids (list of int): the qubit ids involved in the command we're examining.
            commandidcs (list of int): command position in qubit idx's command list.
            inverse_command (Command): the command to be cancelled with.
            apply_commutation (bool): True/False depending on whether optimizer 
                is considering commutation rules. 

        """
        erase = True
        # We dont want to examine qubit idx because the optimizer 
        # has already checked that the gates between the current 
        # and mergeable gates are commutable (or a commutable list).
        commandidcs.pop(qubitids.index(idx)) # Remove corresponding 
        # position of command for qubit idx from commandidcs
        qubitids.remove(idx) # Remove qubitid representing the current 
        # qubit in optimizer
        x=1
        for j in range(len(qubitids)):
            # Check that any gates between current gate and inverse
            # gate are all commutable
            this_command = self._l[qubitids[j]][commandidcs[j]]
            future_command = self._l[qubitids[j]][commandidcs[j]+x]
            while (future_command!=inverse_command):
                if apply_commutation==False:
                    # If apply_commutation turned off, you should 
                    # only get erase=True if commands are next to
                    # eachother on all qubits. i.e. if future_command
                    # and inverse_command are not equal (i.e. there
                    # are gates separating them), you don't want 
                    # optimizer to look at whether the separating gates 
                    # are commutable.
                    return False
                if (this_command.is_commutable(future_command)==1):
                    x+=1
                    future_command = self._l[qubitids[j]][commandidcs[j]+x]
                    erase = True
                else:
                    erase = False
                    break
            if (this_command.is_commutable(future_command)==2):
                new_x = self._check_for_commutable_circuit(this_command, future_command, qubitids[j], commandidcs[j], 0)
                if(new_x>x):
                    x=new_x
                    future_command = self._l[qubitids[j]][commandidcs[j]+x]
                    erase=True
                else:
                    erase=False
                    break
        return erase

    def _can_merge_by_commutation(self, idx, qubitids, commandidcs, merged_command, apply_commutation):
        """
        Determines whether mergeable commands should be merged
        with one another. i.e. the commands between the pair are all
        commutable for each qubit involved in the command.

        Args: 
            idx (int): qubit index
            qubitids (list of int): the qubit ids involved in the command we're examining.
            commandidcs (list of int): command position in qubit idx's command list.
            merged_command (Command): the merged command we want to produce.
            apply_commutation (bool): True/False depending on whether optimizer 
                is considering commutation rules.   
        """
        merge = True
        # We dont want to examine qubit idx because the optimizer has already
        # checked that the gates between the current and mergeable gates are
        # commutable (or a commutable list).
        commandidcs.pop(qubitids.index(idx)) # Remove corresponding position of command for qubit idx from commandidcs
        qubitids.remove(idx) # Remove qubitid representing the current qubit in optimizer
        for j in range(len(qubitids)):
            # Check that any gates between current gate and mergeable
            # gate are commutable
            this_command = self._l[qubitids[j]][commandidcs[j]]
            possible_command = None
            merge = True
            x=1
            while (possible_command!=merged_command):
                if not apply_commutation:
                    # If apply_commutation turned off, you should 
                    # only get erase=True if commands are next to
                    # eachother on all qubits.
                    return False
                future_command = self._l[qubitids[j]][commandidcs[j]+x]
                try:
                    possible_command = this_command.get_merged(future_command)
                except:
                    pass
                if (possible_command==merged_command):
                    merge = True
                    break
                if (this_command.is_commutable(future_command)==1): 
                    x+=1
                    merge = True
                    continue
                else:
                    merge = False
                    break
        return merge

    def _check_for_commutable_circuit(self, command_i, next_command, idx, i, x):
        """ 
        Checks if there is a commutable circuit separating two commands.
        
        Args:
            command_i (Command) = current command
            next_command (Command) = the next command
            idx (int) = index of the current qubit in the optimizer
            i (int) = index of the current command in the optimizer
            x (int) = number of commutable gates infront of i we have found 
                (if there is a commutable circuit, we pretend we have found
                x commutable gates where x is the length of the commutable circuit.) 
        
        Returns: 
            x (int): If there is a commutable circuit the function returns the length x.
                Otherwise, returns 0. 
                
                """
        # commutable_circuit_list is a temp variable just used to create relative_commutable_circuits
        commutable_circuit_list = command_i.gate.get_commutable_circuit_list(n=len(command_i._control_qubits), )
        relative_commutable_circuits = []
        # Keep a list of circuits that start with 
        # next_command.
        for relative_circuit in commutable_circuit_list:
            if type(relative_circuit[0].gate) is type(next_command.gate):
                relative_commutable_circuits.append(relative_circuit)
        # Create dictionaries { absolute_qubit_idx : relative_qubit_idx }
        # For the purposes of fast lookup, also { relative_qubit_idx : absolute_qubit_idx }
        abs_to_rel = { idx : 0 }
        rel_to_abs = { 0 : idx }
        # If the current command is a CNOT, we set the target qubit idx
        # to 0
        if isinstance(command_i.gate, XGate):
            if len(command_i._control_qubits)==1:
                # At this point we know we have a CNOT
                # we reset the dictionaries so that the
                # target qubit in the abs dictionary 
                # corresponds to the target qubit in the 
                # rel dictionary
                abs_to_rel = {command_i.qubits[0][0].id : 0}
                rel_to_abs = {0 : command_i.qubits[0][0].id}
        y=0 
        absolute_circuit = self._l[idx][i+x+1:]
        # If no (more) relative commutable circuits to check against, 
        # break out of this while loop and move on to next command_i.
        while relative_commutable_circuits:
            # If all the viable relative_circuits have been deleted
            # you want to just move on
            relative_circuit = relative_commutable_circuits[0]
            while (y<len(relative_circuit)):
                # Check that there are still gates in the
                # engine buffer
                if (y>(len(absolute_circuit)-1)):
                    # The absolute circuit is too short to match the relative_circuit
                    # i.e. if the absolute circuit is of len=3, you can't have absolute_circuit[3]
                    # only absolute_circuit[0] - absolute_circuit[2]
                    if relative_commutable_circuits:
                        relative_commutable_circuits.pop(0)
                    break
                # Check if relative_circuit command
                # matches the absolute_circuit command
                next_command = absolute_circuit[y]
                if not type(relative_circuit[y]._gate) is type(next_command.gate):
                    if relative_commutable_circuits:
                        relative_commutable_circuits.pop(0)
                    break

                # Now we know the gates are equal.
                # We check the idcs don't contradict our dictionaries.
                # remember next_command = absolute_circuit[y].
                for qubit in next_command.qubits:
                    # We know a and r should correspond in both dictionaries.
                    a=qubit[0].id
                    r=relative_circuit[y].relative_qubit_idcs[0]
                    if a in abs_to_rel.keys():
                        # If a in abs_to_rel, r will be in rel_to_abs
                        if (abs_to_rel[a] != r):                      
                            if relative_commutable_circuits:
                                relative_commutable_circuits.pop(0)
                            break
                    if r in rel_to_abs.keys():
                        if (rel_to_abs[r] != a):
                            if relative_commutable_circuits:
                                relative_commutable_circuits.pop(0)
                            break
                    abs_to_rel[a] = r
                    rel_to_abs[r] = a
                if not relative_commutable_circuits:
                    break
                # HERE: we know the qubit idcs don't contradict our dictionaries.
                for ctrl_qubit in next_command.control_qubits:
                    # We know a and r should correspond in both dictionaries.
                    a=ctrl_qubit.id
                    r=relative_circuit[y].relative_ctrl_idcs[0]
                    if a in abs_to_rel.keys():
                        # If a in abs_to_rel, r will be in rel_to_abs
                        if (abs_to_rel[a] != r):                       
                            if relative_commutable_circuits:
                                relative_commutable_circuits.pop(0)
                            break
                    if r in rel_to_abs.keys():
                        if (rel_to_abs[r] != a):                
                            if relative_commutable_circuits:
                                relative_commutable_circuits.pop(0)
                            break
                    abs_to_rel[a] = r
                    rel_to_abs[r] = a
                if not relative_commutable_circuits:
                    break
                # HERE: we know all relative/absolute qubits/ctrl qubits do not 
                # contradict dictionaries and are assigned.
                y+=1
            if (y==len(relative_circuit)):
            # Up to the yth term in relative_circuit, we have checked
            # that absolute_circuit[y] == relative_circuit[y]
            # This means absolute_circuit is commutable 
            # with command_i
                # Set x = x+len(relative_circuit)-1 and continue through 
                # while loop as though the list was a commutable gate
                x+=(len(relative_circuit))
                relative_commutable_circuits=[]
                return x
        return x

    def _optimize(self, idx, lim=None):
        """
        Try to remove identity gates using the is_identity function, 
        then merge or even cancel successive gates using the get_merged and
        get_inverse functions of the gate (see, e.g., BasicRotationGate).
        It does so for all qubit command lists.
        """
        # loop over all qubit indices
        i = 0
        limit = len(self._l[idx])
        if lim is not None:
            limit = lim

        while i < limit - 1:
            command_i = self._l[idx][i]

            # Delete command i if it is equivalent to identity
            if command_i.is_identity():
                self._delete_command(idx, i)
                i = 0
                limit -= 1
                continue
            
            x = 0
            while (i+x+1 < limit):
                # At this point:
                # Gate i is commutable with each gate up to i+x, so 
                # check if i and i+x+1 can be cancelled or merged
                inv = self._l[idx][i].get_inverse()
                if inv == self._l[idx][i+x+1]:
                    # List of the indices of the qubits that are involved
                    # in command
                    qubitids = [qb.id for sublist in self._l[idx][i].all_qubits
                        for qb in sublist]
                    # List of the command indices corresponding to the position
                    # of this command on each qubit id 
                    commandidcs = self._get_gate_indices(idx, i, qubitids)
                    erase = self._can_cancel_by_commutation(idx, qubitids, commandidcs, inv, self._apply_commutation)
                    if erase:
                    # Delete the inverse commands. Delete the later
                    # one first so the first index doesn't 
                    # change before you delete it.
                        self._delete_command(idx, i+x+1)
                        self._delete_command(idx, i)
                        i = 0
                        limit -= 2
                        break
                try:
                    merged_command = self._l[idx][i].get_merged(self._l[idx][i+x+1])
                    # determine index of this gate on all qubits
                    qubitids = [qb.id for sublist in self._l[idx][i].all_qubits
                                for qb in sublist]
                    commandidcs = self._get_gate_indices(idx, i, qubitids)
                    merge = self._can_merge_by_commutation(idx, qubitids, commandidcs, 
                                                            merged_command, self._apply_commutation)
                    if merge:
                        # Delete command i+x+1 first because i+x+1
                        # will not affect index of i
                        self._delete_command(idx, i+x+1)
                        self._replace_command(idx, i, merged_command)
                        i = 0
                        limit -= 1
                        break
                except NotMergeable:
                    # Unsuccessful in merging, see if gates are commutable
                    pass

                # If apply_commutation=False, then we want the optimizer to 
                # ignore commutation when optimizing
                if not self._apply_commutation:
                    break
                command_i = self._l[idx][i]
                next_command = self._l[idx][i+x+1]
                #----------------------------------------------------------#
                # See if next_command is commutable with this_command.     #                      #
                #----------------------------------------------------------#
                commutability_check = command_i.is_commutable(next_command)
                if(commutability_check == Commutability.COMMUTABLE):
                    x=x+1
                    continue

                #----------------------------------------------------------#
                # See if next_command is part of a circuit which is        #
                # commutable with this_command.                            #
                #----------------------------------------------------------#
                new_x = 0
                if(commutability_check == Commutability.MAYBE_COMMUTABLE):
                    new_x = self._check_for_commutable_circuit(command_i, next_command, idx, i, x)  
                if(new_x>x):
                    x=new_x
                    continue
                else:
                    break
            i += 1  # next iteration: look at next gate
        return limit

    def _check_and_send(self):
        """
        Check whether a qubit pipeline must be sent on and, if so,
        optimize the pipeline and then send it on.
        """
        for i in self._l:
            if (len(self._l[i]) >= self._m or len(self._l[i]) > 0 and
                    isinstance(self._l[i][-1].gate, FastForwardingGate)):
                self._optimize(i)
                if (len(self._l[i]) >= self._m and not
                        isinstance(self._l[i][-1].gate,
                                   FastForwardingGate)):
                    self._send_qubit_pipeline(i, len(self._l[i]) - self._m + 1)
                elif (len(self._l[i]) > 0 and
                      isinstance(self._l[i][-1].gate, FastForwardingGate)):
                    self._send_qubit_pipeline(i, len(self._l[i]))
        new_dict = dict()
        for idx in self._l:
            if len(self._l[idx]) > 0:
                new_dict[idx] = self._l[idx]
        self._l = new_dict

    def _cache_cmd(self, cmd):
        """
        Cache a command, i.e., inserts it into the command lists of all qubits
        involved.
        """
        # are there qubit ids that haven't been added to the list?
        idlist = [qubit.id for sublist in cmd.all_qubits for qubit in sublist]

        # add gate command to each of the qubits involved
        for ID in idlist:
            if ID not in self._l:
                self._l[ID] = []
            self._l[ID] += [cmd]

        self._check_and_send()

    def receive(self, command_list):
        """
        Receive commands from the previous engine and cache them.
        If a flush gate arrives, the entire buffer is sent on.
        """
        for cmd in command_list:
            if cmd.gate == FlushGate():  # flush gate --> optimize and flush
                for idx in self._l:
                    self._optimize(idx)
                    self._send_qubit_pipeline(idx, len(self._l[idx]))
                new_dict = dict()
                for idx in self._l:
                    if len(self._l[idx]) > 0:
                        new_dict[idx] = self._l[idx]
                self._l = new_dict
                assert self._l == dict()
                self.send([cmd])
            else:
                self._cache_cmd(cmd)